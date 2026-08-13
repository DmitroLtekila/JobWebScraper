import asyncio
import json

import psycopg
import psycopg_pool


connect = "dbname=jobdata user=postgres password=1234 host=localhost port=5432"

async def get_all_jobs(pool):
    result = []
    async with pool.connection() as conn:
            async with conn.cursor() as acur:
                await acur.execute("""
                SELECT extracted_data -> 'url', extracted_data -> 'technologies_with_years'
                FROM analysed_data
                """)
                async for row in acur:
                    result += [{"url": row[0], "technologies": row[1]}]
            
    return result
async def get_amount_of_jobs(pool):
    result = 0
    async with pool.connection() as conn:
            async with conn.cursor() as acur:
                await acur.execute("""
                SELECT COUNT(*)
                FROM analysed_data
                """)
                async for row in acur:
                    result = row[0]
    return result

async def get_all_jobs_data():
    async with psycopg_pool.AsyncConnectionPool(connect, max_size=15) as pool:
        result = await get_all_jobs(pool)
        total_jobs = await get_amount_of_jobs(pool)
    with open("top_technologies.json", "r") as f:
            json_data = json.load(f)
    valid_jobs = []
    for item in result:
        for tech in item["technologies"]:
            if tech['technology'] in json_data.keys():
                valid_jobs.append(item)
                break
                
    
    # print(json_data)
    # print(result)
    print(len(valid_jobs))
    print(total_jobs)


if __name__=="__main__":
    # asyncio.run(add_to_df())
    asyncio.run(get_all_jobs_data())