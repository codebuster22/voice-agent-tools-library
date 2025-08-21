from calendar_tools import create_service
import asyncio
import os
import dotenv

dotenv.load_dotenv()
email = os.getenv("EMAIL_FOR_TESTING")

async def main():
    # Email from .env or parameter
    service = await create_service(email)
    print(service)

if __name__ == "__main__":
    asyncio.run(main())