import time
import sys
import os
import json
import asyncio
import httpx
from typing import List, Dict, Any
from contextlib import AsyncExitStack

# Internal imports
from data.market_data import MarketDataFetcher
from data.news_scraper import NewsFetcher
from data.database import DatabaseManager
from trading.broker_client import BrokerClient
from trading.risk_manager import RiskManager

# MCP
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# We want to connect to all MCP servers defined in DB.
async def setup_mcp_sessions(db, exit_stack):
    mcp_servers = db.get_mcp_servers()
    sessions = {}
    for server in mcp_servers:
        env_dict = None
        if server['env_vars']:
            try:
                env_dict = json.loads(server['env_vars'])
            except:
                pass
        
        server_params = StdioServerParameters(
            command=server['command'],
            args=server['args'].split() if server['args'] else [],
            env={**os.environ, **env_dict} if env_dict else None
        )
        try:
            stdio_transport = await exit_stack.enter_async_context(stdio_client(server_params))
            stdio, write = stdio_transport
            session = await exit_stack.enter_async_context(ClientSession(stdio, write))
            await session.initialize()
            sessions[server['name']] = session
        except Exception as e:
            print(f"[MCP] Failed to connect to server {server['name']}: {e}")
            
    return sessions

async def get_mcp_tools(sessions) -> List[Dict]:
    tools = []
    for name, session in sessions.items():
        try:
            res = await session.list_tools()
            for t in res.tools:
                tools.append({
                    "type": "function",
                    "function": {
                        "name": f"{name}___{t.name}", # e.g. alpaca___execute_trade
                        "description": t.description,
                        "parameters": t.inputSchema
                    }
                })
        except Exception as e:
            print(f"[MCP] Failed to fetch tools from {name}: {e}")
    return tools

async def chat_with_llm(messages, tools, base_url, api_key, model_name):
    # Standard OpenAI compatible chat completion
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model_name,
        "messages": messages,
    }
    if tools:
        payload["tools"] = tools
        
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            res = await client.post(f"{base_url}/chat/completions", headers=headers, json=payload)
            res.raise_for_status()
            return res.json()
        except Exception as e:
            print(f"[LLM Error] {e}")
            if hasattr(e, 'response') and e.response:
                print(e.response.text)
            return None

async def execute_mcp_tool(sessions, tool_name: str, args: dict):
    # Parse name, e.g. alpaca___execute_trade
    parts = tool_name.split("___", 1)
    if len(parts) != 2:
        return f"Error: Malformed tool name {tool_name}"
    
    server_name, actual_tool_name = parts
    session = sessions.get(server_name)
    if not session:
        return f"Error: MCP Server {server_name} not found."
    
    try:
        res = await session.call_tool(actual_tool_name, arguments=args)
        # res is a CallToolResult having 'content' list
        out = ""
        for content in res.content:
            if content.type == "text":
                out += content.text
        return out
    except Exception as e:
        return f"Error executing tool {tool_name}: {str(e)}"

async def async_main():
    if sys.platform == "win32":
        try:
            import codecs
            sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
        except Exception:
            pass

    print("Starting AI Agent Trading Bot with MCP Integration...")
    
    db = DatabaseManager()
    market_fetcher = MarketDataFetcher()
    news_fetcher = NewsFetcher()
    broker = BrokerClient()
    risk_manager = RiskManager()
    
    while True:
        try:
            tickers_to_watch = db.get_watchlist()
            provider = db.get_setting('llm_provider')
            base_url = db.get_setting('llm_base_url') or "https://api.openai.com/v1"
            model_name = db.get_setting('llm_model') or "gpt-4o"
            api_key = db.get_setting('llm_api_key') or ""
            
            print(f"\n--- New Trading Cycle - Balance: ${broker.get_account_balance():.2f} ---")
            
            if provider != "openai":
                print("Agentic MCP loop requires an LLM provider set to 'Universal OpenAI Compatible API' to parse tool calls.")
                print("Please update Settings in the dashboard.")
                await asyncio.sleep(10)
                continue
                
            if not tickers_to_watch:
                print("Watchlist empty. Add tickers via the Dashboard Settings tab.")
                await asyncio.sleep(10)
                continue
                
            async with AsyncExitStack() as exit_stack:
                print("[MCP] Initializing MCP connections...")
                sessions = await setup_mcp_sessions(db, exit_stack)
                system_tools = await get_mcp_tools(sessions)
                
                print(f"[MCP] Loaded {len(system_tools)} external tools.")
                
                for ticker in tickers_to_watch:
                    print(f"\n--- Agent analyzing {ticker} ---")
                    
                    df = market_fetcher.fetch_historical_stock_data(ticker, period="1mo", interval="1d")
                    if df.empty:
                        continue
                        
                    current_price = df['Close'].iloc[-1]
                    news_items = news_fetcher.fetch_recent_news(ticker, days_back=1)
                    news_text = "\n".join([f"- {n['title']}" for n in news_items]) if news_items else "No recent news."
                    
                    system_prompt = f"""You are AstraQuant AI, an autonomous financial agent.
Your objective is to analyze {ticker}. The current price is ${current_price:.2f}.
Recent News:
{news_text}

Use your provided tools to query further context (like using an external Alpaca MCP server to check positions, fetch fundamental data, or execute trades).
If you have no tools to execute trades, you can print a recommendation.
Think step-by-step.
"""
                    messages = [{"role": "system", "content": system_prompt}]
                    
                    # Agent Loop (max 5 steps)
                    for step in range(5):
                        print(f"[{ticker}] Agent thinking (Step {step+1})...")
                        response_json = await chat_with_llm(messages, system_tools, base_url, api_key, model_name)
                        
                        if not response_json or "choices" not in response_json:
                            print(f"[{ticker}] Agent failed to respond or API error occurred.")
                            break
                            
                        message = response_json["choices"][0]["message"]
                        messages.append(message)
                        
                        if "tool_calls" not in message or not message["tool_calls"]:
                            print(f"[{ticker}] Agent finalized its output:\n{message.get('content')}")
                            break # Agent finished
                            
                        # Execute Tool Calls
                        for tool_call in message["tool_calls"]:
                            tool_name = tool_call["function"]["name"]
                            tool_args = json.loads(tool_call["function"]["arguments"])
                            
                            print(f"[{ticker}] Executing Tool: {tool_name}({tool_args})")
                            tool_result = await execute_mcp_tool(sessions, tool_name, tool_args)
                            print(f"[Tool Result]: {str(tool_result)[:200]}...")
                            
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call["id"],
                                "content": str(tool_result),
                                "name": tool_name
                            })
                            
            print("Cycle complete. Waiting for next interval...")
            await asyncio.sleep(3600)
            
        except KeyboardInterrupt:
            print("Bot stopped by user.")
            break
        except Exception as e:
            print(f"Error in main loop: {e}")
            import traceback
            traceback.print_exc()
            await asyncio.sleep(60)

def main():
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        print("Bot stopped.")

if __name__ == "__main__":
    main()
