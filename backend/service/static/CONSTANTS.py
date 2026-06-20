CANDIDATE_TAGS = [
    # Necklines (Crucial for tops/dresses)
    "v-neck", "crew neck", "scoop neck", "square neck", "halter neck", 
    "turtleneck", "off-shoulder", "cowl neck", "polo collar",
    
    # Sleeves
    "sleeveless", "short sleeve", "long sleeve", "puff sleeve", 
    "cap sleeve", "bell sleeve", "raglan sleeve",
    
    # Lengths
    "cropped", "mini", "midi", "maxi", "knee-length", "full-length",
    
    # Trousers/Bottoms
    "high-waisted", "low-rise", "wide leg", "straight leg", "tapered", 
    "flared", "bootcut", "cargo",
    
    # Closures/Features
    "button-down", "zipper", "wrap-around", "drawstring", "elastic waist",
    "cut-out", "slit", "peplum", "asymmetric",

    # Patterns/Prints
    "floral", "striped", "polka dot", "plaid", "animal print", "geometric", "paisley", "camouflage",
    "ruched waist", "peplum", "collared", "long sleeve"
]

VINTED_COLOUR_MAP = {
    "Black": "1",
    "Grey": "3",
    "White": "12",
    "Cream": "20",
    "Beige": "4",
    "Apricot": "21",
    "Orange": "11",
    "Coral": "22",
    "Red": "7",
    "Burgundy": "23",
    "Pink": "5",
    "Rose": "24",
    "Purple": "6",
    "Lilac": "25",
    "Light blue": "26",
    "Blue": "9",
    "Navy": "27",
    "Turquoise": "17",
    "Mint": "30",
    "Green": "10",
    "Dark green": "28",
    "Khaki": "16",
    "Brown": "2",
    "Mustard": "29",
    "Yellow": "8",
    "Silver": "13",
    "Gold": "14",
    "Multi": "15",
    "Clear": "32"
}

COLOUR_MAP: dict[str, list[str]] = {
    "Black": [VINTED_COLOUR_MAP["Black"], VINTED_COLOUR_MAP["Grey"]],
    "Grey": [VINTED_COLOUR_MAP["Grey"], VINTED_COLOUR_MAP["Silver"]],
    "White": [VINTED_COLOUR_MAP["White"]],
    "Cream": [VINTED_COLOUR_MAP["Cream"], VINTED_COLOUR_MAP["Beige"]],
    "Orange": [VINTED_COLOUR_MAP["Apricot"], VINTED_COLOUR_MAP["Coral"]],
    "Red": [VINTED_COLOUR_MAP["Red"], VINTED_COLOUR_MAP["Burgundy"]],
    "Pink": [VINTED_COLOUR_MAP["Pink"], VINTED_COLOUR_MAP["Rose"]],
    "Purple": [VINTED_COLOUR_MAP["Purple"], VINTED_COLOUR_MAP["Lilac"]],
    "Blue": [VINTED_COLOUR_MAP["Blue"], VINTED_COLOUR_MAP["Light blue"], VINTED_COLOUR_MAP["Navy"]],
    "Turquoise": [VINTED_COLOUR_MAP["Turquoise"]],
    "Green": [VINTED_COLOUR_MAP["Green"], VINTED_COLOUR_MAP["Dark green"], VINTED_COLOUR_MAP["Mint"], VINTED_COLOUR_MAP["Khaki"]],
    "Brown": [VINTED_COLOUR_MAP["Brown"], VINTED_COLOUR_MAP["Khaki"]],
    "Yellow": [VINTED_COLOUR_MAP["Yellow"], VINTED_COLOUR_MAP["Mustard"], VINTED_COLOUR_MAP["Gold"]],
    "Multi": [VINTED_COLOUR_MAP["Multi"]],
    "Clear": [VINTED_COLOUR_MAP["Clear"]]
}

VINTED_CATEGORY_MAP = {
    "All clothes": "4", 
    "Outerwear": "1037",
    "Jumpers & sweaters": "13",
    "Suits & blazers": "8",
    "Dresses": "10",
    "Skirts": "11",
    "Skorts": "5491",
    "Tops & t-shirts": "12",
    "Jeans": "183",
    "Trousers & leggings": "9",
    "Shorts & cropped trousers": "15",
    "Jumpsuits & playsuits": "1035",
    "Swimwear": "28",
    "Lingerie & nightwear": "29",
    "Maternity clothes": "1176",
    "Activewear": "73",
    "Shoes": "16",
    "Bags": "19"
}

CATEGORY_HIERARCHY = {
    "top, shirt, blouse": ["Tops & t-shirts", "Jumpers & sweaters", "Outerwear"],
    "trousers, pants, jeans": ["Jeans", "Trousers & leggings", "Shorts & cropped trousers"],
    "dress, skirt": ["Dresses", "Skirts", "Skorts", "Jumpsuits & playsuits"],
    "shoes, boots, sandals": ["Shoes"],
    "bag, purse, wallet": ["Bags"]
}

VINTED_WOMENS_SIZE_MAP = {
    "XXXS / UK 0": "1226",
    "XXS / UK 2": "102",
    "XS / UK 4-6": "2",
    "S / UK 8-10": "3",
    "M / UK 12-14": "4",
    "L / UK 16-18": "5",
    "XL / UK 20-22": "6",
    "XXL / UK 24-26": "7",
    "XXXL / UK 28-30": "310",
    "4XL / UK 32-34": "311",
    "5XL / UK 36-38": "312",
    "6XL / UK 40-42": "1227",
    "7XL / UK 44-46": "1228",
    "8XL / UK 48-50": "1229",
    "9XL / UK 52": "1230",
    "One size": "90",
    "Other": "97"
}