"""
Regional context mapping for language-specific cultural references
"""
from typing import Dict, List

# Language code to regional context mapping
LANGUAGE_REGIONAL_CONTEXT: Dict[str, Dict[str, any]] = {
    "hi": {  # Hindi
        "regions": ["North India", "Delhi NCR", "Uttar Pradesh", "Haryana", "Rajasthan", "Madhya Pradesh", "Bihar", "Jharkhand"],
        "major_cities": ["Delhi", "Mumbai", "Jaipur", "Lucknow", "Kanpur"],
        "cultural_references": [
            "Holi and Diwali celebrations",
            "Cricket matches at Wankhede Stadium",
            "Delhi Metro as daily commute",
            "Street food like golgappa and chaat",
            "Bollywood movies and songs"
        ],
        "business_examples": [
            "Reliance Industries",
            "Tata Group",
            "Indian Railways",
            "ISRO space missions",
            "Digital India initiatives"
        ],
        "education_references": [
            "IIT entrance exams",
            "NCERT textbooks",
            "Delhi University",
            "Government school system"
        ],
        "local_examples": [
            "Traffic on Delhi-Gurgaon expressway",
            "Monsoon season challenges",
            "Power cuts in summer",
            "Local sabzi mandi (vegetable market)"
        ]
    },
    "bn": {  # Bengali
        "regions": ["West Bengal", "Bangladesh", "Kolkata region"],
        "major_cities": ["Kolkata", "Dhaka", "Siliguri"],
        "cultural_references": [
            "Durga Puja celebrations",
            "Rabindra Sangeet music",
            "Howrah Bridge",
            "Rasgulla and mishti doi sweets",
            "Bengali literature and poetry"
        ],
        "business_examples": [
            "Kolkata Port",
            "IT sector in Salt Lake",
            "Tea gardens of Darjeeling",
            "Jute industry"
        ],
        "education_references": [
            "Jadavpur University",
            "Presidency College",
            "West Bengal board exams"
        ],
        "local_examples": [
            "Yellow taxis in Kolkata",
            "Trams on College Street",
            "Maidan gatherings",
            "Adda (casual conversations)"
        ]
    },
    "ta": {  # Tamil
        "regions": ["Tamil Nadu", "Chennai", "Coimbatore", "Madurai"],
        "major_cities": ["Chennai", "Coimbatore", "Madurai", "Trichy"],
        "cultural_references": [
            "Pongal festival",
            "Bharatanatyam dance",
            "Marina Beach walks",
            "Filter coffee tradition",
            "Tamil cinema industry"
        ],
        "business_examples": [
            "Automobile hub in Chennai",
            "Tirupur textile industry",
            "IT corridor in Sholinganallur",
            "Coimbatore manufacturing"
        ],
        "education_references": [
            "IIT Madras",
            "Anna University",
            "Tamil Nadu state board"
        ],
        "local_examples": [
            "MRTS and Metro trains",
            "Kaapi shops on every street",
            "Temple visits on weekends",
            "Kovil festivals"
        ]
    },
    "te": {  # Telugu
        "regions": ["Andhra Pradesh", "Telangana", "Hyderabad"],
        "major_cities": ["Hyderabad", "Visakhapatnam", "Vijayawada", "Guntur"],
        "cultural_references": [
            "Ugadi festival",
            "Biryani culture in Hyderabad",
            "Kuchipudi dance",
            "Charminar landmark",
            "Telugu film industry (Tollywood)"
        ],
        "business_examples": [
            "HITEC City IT hub",
            "Pharmaceutical companies",
            "Visakhapatnam port",
            "Rice production in Godavari delta"
        ],
        "education_references": [
            "IIT Hyderabad",
            "Osmania University",
            "Narayana and Sri Chaitanya coaching"
        ],
        "local_examples": [
            "Hyderabad Metro",
            "Irani chai shops",
            "Tank Bund walks",
            "Old City markets"
        ]
    },
    "mr": {  # Marathi
        "regions": ["Maharashtra", "Mumbai", "Pune", "Nagpur"],
        "major_cities": ["Mumbai", "Pune", "Nagpur", "Nashik"],
        "cultural_references": [
            "Ganesh Chaturthi festival",
            "Lavani folk dance",
            "Gateway of India",
            "Vada pav street food",
            "Marathi theatre and cinema"
        ],
        "business_examples": [
            "Bombay Stock Exchange",
            "Pune IT companies",
            "Mumbai Dabbawalas",
            "Nashik wine industry"
        ],
        "education_references": [
            "IIT Bombay",
            "University of Pune",
            "Mumbai University"
        ],
        "local_examples": [
            "Mumbai local trains",
            "Pune traffic jams",
            "Monsoon flooding in Mumbai",
            "Misal pav for breakfast"
        ]
    },
    "gu": {  # Gujarati
        "regions": ["Gujarat", "Ahmedabad", "Surat", "Vadodara"],
        "major_cities": ["Ahmedabad", "Surat", "Vadodara", "Rajkot"],
        "cultural_references": [
            "Navratri garba dancing",
            "Sabarmati Ashram",
            "Dhokla and fafda snacks",
            "Rann of Kutch",
            "Gujarati business community"
        ],
        "business_examples": [
            "Diamond industry in Surat",
            "Ahmedabad textile mills",
            "Mundra port",
            "Entrepreneurship culture"
        ],
        "education_references": [
            "IIM Ahmedabad",
            "Gujarat University",
            "PDPU Gandhinagar"
        ],
        "local_examples": [
            "BRTS buses in Ahmedabad",
            "Sunday markets",
            "Vegetarian cuisine everywhere",
            "Community trading networks"
        ]
    },
    "kn": {  # Kannada
        "regions": ["Karnataka", "Bangalore", "Mysore", "Mangalore"],
        "major_cities": ["Bangalore", "Mysore", "Hubli", "Mangalore"],
        "cultural_references": [
            "Dasara celebrations in Mysore",
            "Yakshagana theatre",
            "Vidhana Soudha building",
            "Filter coffee and idli",
            "Kannada cinema"
        ],
        "business_examples": [
            "IT companies in Bangalore",
            "Infosys and Wipro headquarters",
            "Coffee plantations in Coorg",
            "Bangalore startup ecosystem"
        ],
        "education_references": [
            "IISc Bangalore",
            "Bangalore University",
            "Karnataka state board"
        ],
        "local_examples": [
            "Bangalore Metro",
            "Traffic on Outer Ring Road",
            "Udupi restaurants",
            "Weekend trips to Nandi Hills"
        ]
    },
    "ml": {  # Malayalam
        "regions": ["Kerala", "Thiruvananthapuram", "Kochi", "Kozhikode"],
        "major_cities": ["Kochi", "Thiruvananthapuram", "Kozhikode", "Thrissur"],
        "cultural_references": [
            "Onam festival",
            "Kathakali dance-drama",
            "Backwaters of Kerala",
            "Banana chips and appam",
            "Malayalam literature"
        ],
        "business_examples": [
            "Kochi port and shipyards",
            "Spice trade",
            "Tourism industry",
            "Gulf remittances economy"
        ],
        "education_references": [
            "100% literacy rate",
            "Kerala University",
            "IIT Palakkad"
        ],
        "local_examples": [
            "Monsoon rains",
            "Bus transport system",
            "Toddy shops",
            "Community reading culture"
        ]
    },
    "pa": {  # Punjabi
        "regions": ["Punjab", "Chandigarh", "Amritsar", "Ludhiana"],
        "major_cities": ["Chandigarh", "Amritsar", "Ludhiana", "Jalandhar"],
        "cultural_references": [
            "Vaisakhi festival",
            "Bhangra and Giddha dances",
            "Golden Temple",
            "Makki di roti and sarson da saag",
            "Punjabi music industry"
        ],
        "business_examples": [
            "Agricultural economy",
            "Ludhiana textile industry",
            "NRI business connections",
            "Sports goods manufacturing"
        ],
        "education_references": [
            "Panjab University Chandigarh",
            "Punjab Agricultural University",
            "Coaching centers for abroad studies"
        ],
        "local_examples": [
            "Farm tractor culture",
            "Dhabas on highways",
            "Cricket and hockey passion",
            "Mandi system for crops"
        ]
    },
    "or": {  # Odia
        "regions": ["Odisha", "Bhubaneswar", "Cuttack", "Puri"],
        "major_cities": ["Bhubaneswar", "Cuttack", "Puri", "Rourkela"],
        "cultural_references": [
            "Rath Yatra in Puri",
            "Odissi classical dance",
            "Konark Sun Temple",
            "Rasagola (sweet)",
            "Jagannath temple traditions"
        ],
        "business_examples": [
            "Steel plants in Rourkela",
            "Mining industry",
            "Chilika Lake fisheries",
            "Handicrafts and textiles"
        ],
        "education_references": [
            "IIT Bhubaneswar",
            "Utkal University",
            "Odisha state board"
        ],
        "local_examples": [
            "Cyclone preparedness",
            "Beach festivals",
            "Temple architecture",
            "Traditional boat races"
        ]
    },
    "en": {  # English (Indian context)
        "regions": ["Pan-India", "Metro cities", "Urban India"],
        "major_cities": ["Delhi", "Mumbai", "Bangalore", "Chennai", "Kolkata", "Hyderabad"],
        "cultural_references": [
            "Indian festivals (Diwali, Holi, Eid)",
            "Cricket IPL matches",
            "Bollywood and regional cinema",
            "Indian street food culture",
            "Diverse cultural heritage"
        ],
        "business_examples": [
            "Indian IT industry",
            "Startup India ecosystem",
            "Digital payment revolution (UPI)",
            "E-commerce growth",
            "Make in India initiatives"
        ],
        "education_references": [
            "IITs and IIMs",
            "Central universities",
            "CBSE and ICSE boards",
            "Competitive exam culture"
        ],
        "local_examples": [
            "Metro trains in major cities",
            "Traffic congestion",
            "Monsoon season challenges",
            "Chai and samosa breaks"
        ]
    }
}


def get_regional_context(language_code: str) -> Dict[str, any]:
    """
    Get regional context for a given language code
    
    Args:
        language_code: Language code (e.g., 'hi', 'ta', 'bn')
    
    Returns:
        Dictionary with regional context information
    """
    return LANGUAGE_REGIONAL_CONTEXT.get(language_code, LANGUAGE_REGIONAL_CONTEXT["en"])


def get_regional_prompt_enhancement(language_code: str) -> str:
    """
    Generate prompt enhancement text with regional context
    
    Args:
        language_code: Language code
    
    Returns:
        String to add to LLM prompt for regional context
    """
    context = get_regional_context(language_code)
    
    return f"""
REGIONAL CONTEXT for {language_code.upper()}:
- Target Regions: {', '.join(context['regions'])}
- Major Cities: {', '.join(context['major_cities'])}

When providing examples, use references that resonate with people from these regions:
- Cultural: {', '.join(context['cultural_references'][:3])}
- Business: {', '.join(context['business_examples'][:3])}
- Daily Life: {', '.join(context['local_examples'][:3])}

Make the explanation relatable by using familiar landmarks, festivals, businesses, or daily experiences from these regions.
"""
