# Personal Care Ingredients Parser Project
An effort to develop a system to parse a personal care product's ingredients label and provide both a breakdown of the ingredient souces (vegetable/animal/mineral/water), and the overall safety of the product given the ingredients.

---

References:
https://www.mariegale.com/quick-labeling-faq/


-----

## Talk Abstract, Proposed to PyCascades 2020
Full abstract: Modern skin care and hygiene products, like soaps, lotions, and deodorants, often contain a large number of ingredients with complex names. It's often unclear at a single glance what the source of the ingredients are, and whether they're safe to use. So let's develop a system to parse an ingredient label and provide both a breakdown of the ingredient souces (vegetable/animal/mineral/water), and the overall safety of the product given the ingredients. We'll examine python packages and methods associated with OCR, databases, and webscraping, as well as a discussion of the assumptions and problems in developing these kinds of categorizations. Along the way, we'll discuss the history of cosmetics and personal care ingredients, differences in modern regulations around the world and safety implications, and why only looking at ingredients lists is often not sufficient to understand the full picture of where your modern comfort might originate. All experience levels welcome.

---

Proposed breakdown (May wind up adjusting to spend more time on project portion):
	
- Talk intro (1 minutes)
-  History of ingredients used in skin care, soap, and other personal care products (2 minutes)
- Modern US approach to regulation cosmetics ingredients (2 min)
    - And contrast with world-wide approach
    - E.g. Only 9 chemicals banned by the FDA since the 1930s, vs 1400 chemicals banned in other countries worldwide. (https://www.ewg.org/news-and-analysis/2019/03/cosmetics-safety-us-trails-more-40-nations)
		
- Examples of existing product apps: The Why (2 min)
    - EWG's SkinDeep Guide  (https://www.ewg.org/skindeep/)
        - To understand the safety of ingredients/products.
    - "Cruelty Cutter" and "Is it Vegan" apps
        - To understand and avoid ingredients people have an ethical objections to 
        - To determine if a company tests on animals
		
- Existing product parsers: The How (2 min)
    - Ingredient label-based
        -  Either a upload a list of ingredients, or a picture of a list of ingredients, and get back a measure based on the components
    - UPC-based
        - A database collects information on each product, tied to its UPC. Users upload the upc and download the 
        - The examples listed above are all product-based. 

- Our project: let's combine ingredients-based approach and include both a safety rating, and a ingredient source breakdown. This is where I'll get into outlining packages/code used.
    -  OCR portion: going from photo of ingredients to a neat list of parsed ingredients (3 min)
    - Grabbing ingredient data (4 min)
        - Which databases to use and how to choose what to include
    - How to combine the data (3 min)
        -  What happens if a chemical can be made in multiple ways?
        - What if there is conflicting data about safety?
    - How to store and retrieve data for our app (4 min)
        - Choosing SQL vs NoSQL vs flat file, etc
        - What data to display and how (Dashboarding/rendering/front end)
			
- Why this is not the full picture - why we can only determine so much from an ingredients list, and how we can be the most informed consumers we can be. (2 min)
	
