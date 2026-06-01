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
load_dotenv()

api_key = os.getenv("API_KEY")

from enum import Enum

# Four dimensions for analysis
# company_domain
# company_subdomain
# job_function
# data_focus


class CompanyDomain(str, Enum):
    TECHNOLOGY_SOFTWARE = "technology_software"
    IT_SERVICES_CONSULTING = "it_services_consulting"

    BANKING_FINTECH = "banking_fintech"
    INSURANCE = "insurance"

    ECOMMERCE_MARKETPLACE = "ecommerce_marketplace"
    RETAIL_CONSUMER_GOODS = "retail_consumer_goods"

    MANUFACTURING = "manufacturing"
    LOGISTICS_SUPPLY_CHAIN = "logistics_supply_chain"
    TRANSPORT_AVIATION = "transport_aviation"

    HEALTHCARE_PHARMA = "healthcare_pharma"

    ENERGY_UTILITIES = "energy_utilities"

    TELECOMMUNICATIONS = "telecommunications"

    PUBLIC_SECTOR = "public_sector"

    MEDIA_MARKETING = "media_marketing"

    EDUCATION = "education"

    OTHER = "other"
class CompanySubdomain(str, Enum):

    # Technology
    SAAS_PLATFORM = "saas_platform"
    ENTERPRISE_SOFTWARE = "enterprise_software"
    DATA_PLATFORM = "data_platform"
    AI_PLATFORM = "ai_platform"
    CYBERSECURITY = "cybersecurity"
    CLOUD_SERVICES = "cloud_services"
    DEVOPS_PLATFORM = "devops_platform"

    # Consulting
    DATA_CONSULTING = "data_consulting"
    BI_CONSULTING = "bi_consulting"
    DIGITAL_TRANSFORMATION = "digital_transformation"
    IT_OUTSOURCING = "it_outsourcing"

    # Finance
    RETAIL_BANKING = "retail_banking"
    CORPORATE_BANKING = "corporate_banking"
    RISK_ANALYTICS = "risk_analytics"
    REGULATORY_REPORTING = "regulatory_reporting"
    FINANCIAL_ANALYTICS = "financial_analytics"

    # E-commerce
    MARKETPLACE = "marketplace"
    FOOD_DELIVERY = "food_delivery"
    ONLINE_RETAIL = "online_retail"
    CUSTOMER_ANALYTICS = "customer_analytics"
    MARKETING_ANALYTICS = "marketing_analytics"

    # Manufacturing
    FACTORY_OPERATIONS = "factory_operations"
    MES_SYSTEMS = "mes_systems"
    INDUSTRIAL_ANALYTICS = "industrial_analytics"
    PRODUCTION_PLANNING = "production_planning"
    SUPPLY_CHAIN_ANALYTICS = "supply_chain_analytics"
    QUALITY_MANAGEMENT = "quality_management"

    # Logistics
    WAREHOUSING = "warehousing"
    TRANSPORT_OPERATIONS = "transport_operations"

    # Aviation
    AIRLINE_OPERATIONS = "airline_operations"
    AIRPORT_OPERATIONS = "airport_operations"

    # Healthcare
    HOSPITAL_OPERATIONS = "hospital_operations"
    MEDICAL_ANALYTICS = "medical_analytics"
    HEALTHCARE_AUDIT = "healthcare_audit"
    PUBLIC_HEALTH = "public_health"

    # Energy
    REFINERY_OPERATIONS = "refinery_operations"
    ENERGY_TRADING = "energy_trading"
    UTILITY_OPERATIONS = "utility_operations"

    # Telecom
    NETWORK_ANALYTICS = "network_analytics"
    TELECOM_OPERATIONS = "telecom_operations"

    # Public sector
    GOVERNMENT_DIGITALIZATION = "government_digitalization"
    PUBLIC_ADMINISTRATION = "public_administration"

    OTHER = "other"
class JobFunction(str, Enum):

    # Analytics
    DATA_ANALYST = "data_analyst"
    BUSINESS_ANALYST = "business_analyst"
    PRODUCT_ANALYST = "product_analyst"
    FINANCIAL_ANALYST = "financial_analyst"
    REPORTING_ANALYST = "reporting_analyst"
    RISK_ANALYST = "risk_analyst"

    # BI
    BI_ANALYST = "bi_analyst"
    BI_DEVELOPER = "bi_developer"
    POWER_BI_ENGINEER = "power_bi_engineer"

    # Engineering
    DATA_ENGINEER = "data_engineer"
    BIG_DATA_ENGINEER = "big_data_engineer"
    ANALYTICS_ENGINEER = "analytics_engineer"
    DATA_WAREHOUSE_ENGINEER = "data_warehouse_engineer"

    # Architecture
    DATA_ARCHITECT = "data_architect"
    SOLUTION_ARCHITECT = "solution_architect"

    # Governance
    DATA_GOVERNANCE = "data_governance"
    DATA_QUALITY = "data_quality"

    # AI
    DATA_SCIENTIST = "data_scientist"
    MACHINE_LEARNING_ENGINEER = "machine_learning_engineer"
    AI_ENGINEER = "ai_engineer"
    MLOPS_ENGINEER = "mlops_engineer"

    # Systems
    SYSTEM_ANALYST = "system_analyst"
    APPLICATION_SUPPORT = "application_support"

    # Automation
    RPA_ENGINEER = "rpa_engineer"

    OTHER = "other"
class DataFocus(str, Enum):

    REPORTING = "reporting"

    DASHBOARDS = "dashboards"

    ETL_ELT = "etl_elt"

    DATA_WAREHOUSING = "data_warehousing"

    DATA_MODELING = "data_modeling"

    DATA_GOVERNANCE = "data_governance"

    DATA_QUALITY = "data_quality"

    MASTER_DATA = "master_data"

    STREAMING_DATA = "streaming_data"

    BIG_DATA = "big_data"

    MACHINE_LEARNING = "machine_learning"

    GENERATIVE_AI = "generative_ai"

    BUSINESS_PROCESS_ANALYSIS = "business_process_analysis"

    RISK_ANALYTICS = "risk_analytics"

    FINANCIAL_REPORTING = "financial_reporting"

    CUSTOMER_ANALYTICS = "customer_analytics"

    MARKETING_ANALYTICS = "marketing_analytics"

    OPERATIONAL_ANALYTICS = "operational_analytics"

    INDUSTRIAL_ANALYTICS = "industrial_analytics"

    OTHER = "other"

class Technologies(BaseModel):
    technology: str = Field(..., description="technology required for posted job")
    required_years_of_experience: int = Field(-1, description="years of experience required for this technology, if years are not mentioned write -1")

class JobData(BaseModel):
    companyDomain: CompanyDomain = Field(..., description="the most accurate description of the job field")
    companySubdomain: CompanySubdomain = Field(..., description="exact description of job's domain")
    jobFunction: JobFunction = Field(..., description="main type of tasks on this job")
    dataFocus : DataFocus = Field(..., description="main function of the job")
    technologies_with_years: list[Technologies] = Field(description="List of technologies/programming languages required for this job, where this year is just requirement of years of expirience to apply to this work. So param for years should be the same for all technologies. Don't extract soft skills to this list")

client = instructor.from_provider("openai/gpt-4o-mini", api_key=api_key, async_client=True)

async def get_responce_from_AI(data: str):    
    return await client.create(
        response_model=JobData,
        messages=[
            {
                "role": "system", 
                "content": "You are a precise data engineering engine extracting data from job postings."
            },
            {
                "role": "user", 
                "content": f"Extract structured details from this text:{data}"
            }
        ],
    )
async def get_data_from_db(queue: asyncio.Queue, pool):
    async with pool.connection() as conn:
            async with conn.cursor() as acur:
                await acur.execute("""
                SELECT id, url, benefits, expected_technologies, responsibilities, requirements
                FROM job_data
                WHERE was_parsed=false
                """)
                async for row in acur:
                    id, url, benefits, expected_technologies, responsibilities, requirements = row
                    all_data = f"{benefits} \n {expected_technologies} \n {responsibilities} \n {requirements}"
                    await queue.put((id, url, all_data))
                    
async def ai_task(queue: asyncio.Queue, pool):
    delay = 0.5
    retries = 0
    max_retries = 5
    while retries < max_retries:
        id, url, text = await queue.get()
        try:
            structured_data = await get_responce_from_AI(text)
            
            async with pool.connection() as conn:
                async with conn.cursor() as cur:
                    diction = {
                        "url" : url,
                        "companyDomain" : structured_data.companyDomain,
                        "companySubdomain" : structured_data.companySubdomain,
                        "jobFunction" : structured_data.jobFunction,
                        "dataFocus" : structured_data.dataFocus,
                        "technologies_with_years" : [t.model_dump() for t in structured_data.technologies_with_years]
                    }
                    await cur.execute(
                        """
                        INSERT INTO analysed_data (job_id, extracted_data)
                        VALUES (%(id)s, %(extracted_data)s)
                        ON CONFLICT (job_id) 
                        DO UPDATE SET extracted_data = EXCLUDED.extracted_data;
                        """,
                        {                   
                            # 'extracted_data': f"{structured_data.soft_business_skills} \n {structured_data.technologies_with_years}"
                            'id' : id,
                            'extracted_data' : json.dumps(diction),
                            
                        }
                    )
                    await cur.execute("""UPDATE job_data SET was_parsed=true WHERE id=%(id)s""",
                            {'id': id})
        except Exception as e:
            if retries >= max_retries:
                break
            delay = delay * 2 + random.uniform(0, 0.5)
            retries += 1
            await asyncio.sleep(delay)
            print(f"Error processing job {id}: {e}")
        finally:
            print("All good, parsed job with id: ", id)
            queue.task_done()