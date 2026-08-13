from multiprocessing import pool
import os
import random
import re
import asyncio
import pandas as pd
import psycopg
import psycopg_pool
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import httpx
import curl_cffi
from curl_cffi import AsyncSession
from curl_cffi.requests.exceptions import HTTPError
from openai import OpenAI
from pydantic import BaseModel, Field
import instructor
import json
import os
from enum import Enum
from dotenv import load_dotenv
import time
from collections import OrderedDict


load_dotenv()

api_key = os.getenv("API_KEY")

class Technologies(BaseModel):
    technology: str = Field(..., description="find similar names for technologies, e.g. Power Bi, Microsoft Power BI, MS Excel, Microsoft Excel, PL/SQL, SQL etc., and for similar names return the short one, so Just Excel, Power Bi, SQL.")
    count: int = Field(..., description="count of technologies. It stays the same")
class TechnologiesList(BaseModel):
    technologies: list[Technologies] = Field(..., description="list of technologies with counts")

async def list_of_unique_technologies(pool):
    result = []
    async with pool.connection() as conn:
            async with conn.cursor() as acur:
                await acur.execute("""
                SELECT DISTINCT techno ->> 'technology' AS technology_name, COUNT(*)
                FROM analysed_data,
                LATERAL jsonb_array_elements(extracted_data -> 'technologies_with_years') AS techno
                GROUP BY technology_name
                ORDER BY COUNT(*) DESC
                LIMIT 50
                """)
                async for row in acur:
                    result += [{"technology": row[0], "count": row[1]}]
            
    return result
                    
client = instructor.from_provider("openai/gpt-4o-mini", api_key=api_key, async_client=True)

async def get_responce_from_AI(data: str, response_model):    
    return await client.create(
        response_model=response_model,
        messages=[
            {
                "role": "system", 
                "content": (
                    "You are a precise data engineering engine extracting and grouping data."
                    # "Filter out generic job roles or non-technical terms (e.g., 'data analysis', 'business analysis')."
                    "Return only specific software, languages, or technical frameworks."
                )
            },
            {
                "role": "user", 
                "content": f"Extract structured details from this text:{data}"
            }
        ],
    )

connect = "dbname=jobdata user=postgres password=1234 host=localhost port=5432"

async def add_to_df():
    async with psycopg_pool.AsyncConnectionPool(connect, max_size=15) as pool:
        result = await list_of_unique_technologies(pool)
        
        data_text = "\n".join([f"{item['technology']}: {item['count']}" for item in result])
        
        data = await get_responce_from_AI(data_text, TechnologiesList)
        
        final_result = [item.model_dump() for item in data.technologies]

    ditc = {}
    for item in final_result:
        if item['technology'] not in ditc:
            ditc[item['technology']] = item['count']
        else:
            ditc[item['technology']] += item['count']
    res = OrderedDict(sorted(ditc.items(), key=lambda item: item[1]))
    with open("top_technologies.json", "w") as f:
        json.dump(res, f, indent=4)


async def get_domain(pool):
    result = []
    async with pool.connection() as conn:
            async with conn.cursor() as acur:
                await acur.execute("""
                SELECT extracted_data -> 'companyDomain' AS domain, COUNT(*)	
                FROM analysed_data
                GROUP BY domain
                ORDER BY COUNT(*) DESC
                """)
                async for row in acur:
                    result += [{"companyDomain": row[0], "count": row[1]}]
            
    return result

async def get_domain_data():
    async with psycopg_pool.AsyncConnectionPool(connect, max_size=15) as pool:
        result = await get_domain(pool)
    with open("domains_frequency.json", "w") as f:
        json.dump(result, f, indent=4)


if __name__=="__main__":
    # asyncio.run(add_to_df())
    asyncio.run(get_domain_data())