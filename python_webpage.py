from pyscript import document, web, display, fetch
# from pyscript.fetch import fetch
import json
import asyncio


# div = web.div("Hello, Webbi!")

async def load_data():
            response = await fetch("top_technologies.json")
            data = await response.json()
            sorted_technologies = sorted(data.items(), key=lambda item: item[1], reverse=True)

            container = document.querySelector("#job-container")
            container.innerHTML = ""
            
            for tech, count in sorted_technologies:
                card = document.createElement("div")
                card.className = "job-card"
                
                # Print the technology name and its count dynamically
                card.innerHTML = f"<strong>{tech}</strong>: {count} postings"
            
                container.appendChild(card)
asyncio.ensure_future(load_data())

                