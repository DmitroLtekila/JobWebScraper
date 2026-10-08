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
async def load_info_card():
    container = document.querySelector("#card-list")
    container.innerHTML = ""
    card1 = document.createElement("div")
    card1.className = "info-card"
    card1.innerHTML = "5281 Jobs scanned"
    card2 = document.createElement("div")
    card2.className = "info-card"
    card2.innerHTML = "Most demandend skill - SQL with 1777 postings"
    card3 = document.createElement("div")
    card3.className = "info-card"
    card3.innerHTML = "Top industry sector - IT services-consulting with 1749 postings"
    card4 = document.createElement("div")
    card4.className = "info-card"
    card4.innerHTML = "Displayed top 50 most popular technologies"
    container.appendChild(card1)
    container.appendChild(card2)
    container.appendChild(card3)
    container.appendChild(card4)

asyncio.ensure_future(load_data())
asyncio.ensure_future(load_info_card())
                