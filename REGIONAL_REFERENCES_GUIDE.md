# Regional References Implementation Guide

## 🌏 Overview

Regional references make AI-generated content **culturally relevant and relatable** to specific audiences. Instead of generic examples, the system uses familiar landmarks, festivals, businesses, and daily experiences from the user's region.

---

## 🎯 Why Regional References Matter

### **Generic Example (Without Regional Context):**
> "Machine learning is like learning to ride a bicycle. At first you make mistakes, but with practice you improve."

### **Regional Example (Hindi/North India):**
> "Machine learning ek dum waise hai jaise Delhi Metro mein apna rasta dhoondhna. Pehli baar yellow line, blue line mein confuse ho sakte hain, lekin rozana travel karne se automatic pata chal jata hai ki kahan badalna hai. Bilkul waise hi, AI bhi data se seekh kar apne aap behtar decisions lene lagta hai."

**Translation:** "Machine learning is just like finding your way in Delhi Metro. First time you might get confused between yellow line, blue line, but with daily travel you automatically know where to change. Similarly, AI also learns from data and starts making better decisions automatically."

---

## 📍 Current Implementation

### **1. Language-to-Region Mapping** ✅ IMPLEMENTED

We've created a comprehensive mapping in `constants/regional_context.py` that maps each supported language to:

- **Target Regions**: Geographic areas where the language is spoken
- **Major Cities**: Well-known cities for location-based examples
- **Cultural References**: Festivals, traditions, art forms
- **Business Examples**: Local companies, industries, economic activities
- **Education References**: Schools, universities, exam systems
- **Local Examples**: Daily life scenarios, landmarks, food, transportation

### **Example for Tamil (ta):**
```python
"ta": {
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
        "IT corridor in Sholinganallur"
    ],
    "local_examples": [
        "MRTS and Metro trains",
        "Kaapi shops on every street",
        "Temple visits on weekends"
    ]
}
```

### **2. Enhanced LLM Prompts** ✅ IMPLEMENTED

When `include_regional_references=True`, the system adds specific regional context to the LLM prompt:

```
REGIONAL CONTEXT for TA:
- Target Regions: Tamil Nadu, Chennai, Coimbatore, Madurai
- Major Cities: Chennai, Coimbatore, Madurai, Trichy

When providing examples, use references that resonate with people from these regions:
- Cultural: Pongal festival, Bharatanatyam dance, Marina Beach walks
- Business: Automobile hub in Chennai, Tirupur textile industry, IT corridor
- Daily Life: MRTS and Metro trains, Kaapi shops on every street, Temple visits

Make the explanation relatable by using familiar landmarks, festivals, businesses, 
or daily experiences from these regions.
```

---

## 🚀 Enhancement Approaches

### **Approach 2: Domain-Specific Regional Examples** (RECOMMENDED NEXT)

Add domain-specific mappings for different subject areas:

```python
DOMAIN_REGIONAL_EXAMPLES = {
    "technology": {
        "hi": [
            "Paytm और PhonePe जैसे UPI apps",
            "Flipkart और Amazon की delivery system",
            "Bangalore के IT companies",
            "Digital India initiatives"
        ],
        "ta": [
            "Chennai la irukara IT companies",
            "Zoho Corporation example",
            "TCS and Infosys campus",
            "Tamil Nadu e-Governance"
        ]
    },
    "mathematics": {
        "hi": [
            "Cricket mein run rate calculate karna",
            "Railway ticket ka percentage discount",
            "Sabzi mandi mein weight calculations",
            "EMI payments understanding"
        ],
        "ta": [
            "Kolam patterns la geometry",
            "Temple architecture ratios",
            "Filter coffee proportions",
            "Bus route distance calculations"
        ]
    },
    "science": {
        "hi": [
            "Delhi ki air pollution problem",
            "Monsoon prediction systems",
            "ISRO satellite launches",
            "Ganga river ecosystem"
        ],
        "ta": [
            "Chennai water crisis solutions",
            "Coastal erosion at Marina Beach",
            "Tropical climate of Tamil Nadu",
            "Traditional water harvesting"
        ]
    },
    "business": {
        "hi": [
            "Kirana stores vs D-Mart",
            "Mumbai Dabbawalas efficiency",
            "Amul cooperative model",
            "Reliance Jio disruption"
        ],
        "ta": [
            "Tirupur textile export business",
            "Chennai Port operations",
            "Coimbatore manufacturing cluster",
            "Small-scale foundry industries"
        ]
    }
}
```

**Implementation:**
```python
def get_domain_examples(language_code: str, content: str) -> List[str]:
    """Detect domain from content and return relevant examples"""
    # Simple keyword-based domain detection
    domains = {
        "technology": ["software", "computer", "AI", "digital", "app"],
        "mathematics": ["equation", "calculate", "number", "formula"],
        "science": ["experiment", "hypothesis", "theory", "molecule"],
        "business": ["profit", "market", "company", "sales"]
    }
    
    detected_domain = detect_domain(content, domains)
    return DOMAIN_REGIONAL_EXAMPLES.get(detected_domain, {}).get(language_code, [])
```

---

### **Approach 3: User-Specified Region** (FOR ADVANCED USERS)

Allow users to explicitly specify their region for ultra-personalized references:

**API Enhancement:**
```python
class VoiceNarrationRequest(BaseModel):
    presentation_id: str
    language_code: str = "hi"
    voice_gender: str = "female"
    include_regional_references: bool = True
    student_level: str = "intermediate"
    
    # NEW FIELD
    target_region: Optional[str] = Field(
        description="Specific region/city for localized examples (e.g., 'Delhi', 'Mumbai', 'Chennai')",
        default=None
    )
```

**Region-Specific Context:**
```python
CITY_SPECIFIC_CONTEXT = {
    "Delhi": {
        "transport": ["Metro, DTC buses, auto-rickshaws"],
        "landmarks": ["India Gate, Red Fort, Qutub Minar"],
        "food": ["Chole Bhature, Paranthe Wali Gali"],
        "problems": ["Traffic congestion, air pollution"],
        "strengths": ["Political hub, educational institutions"]
    },
    "Mumbai": {
        "transport": ["Local trains, BEST buses"],
        "landmarks": ["Gateway of India, Marine Drive"],
        "food": ["Vada Pav, Pav Bhaji"],
        "problems": ["Monsoon flooding, housing costs"],
        "strengths": ["Financial capital, Bollywood"]
    },
    "Chennai": {
        "transport": ["MRTS, Metro, MTC buses"],
        "landmarks": ["Marina Beach, Kapaleeshwarar Temple"],
        "food": ["Idli, Dosa, Filter Coffee"],
        "problems": ["Water scarcity, summer heat"],
        "strengths": ["Automobile hub, cultural heritage"]
    }
}
```

---

### **Approach 4: Contextual Code-Mixing** (NATURAL LANGUAGE)

For Indian languages, naturally mix English technical terms (how people actually speak):

**Example for Hindi:**
```
❌ Generic: "वेब डेवलपमेंट में हम HTML और CSS का उपयोग करते हैं"
✅ Natural: "Web development mein hum HTML aur CSS use karte hain, bilkul jaise ek ghar banate waqt pehle structure (HTML) banate hain, phir paint aur decoration (CSS) karte hain"
```

**Implementation:**
```python
CODE_MIXING_GUIDELINES = {
    "hi": "Use Hinglish (Hindi-English mix) for technical terms. Keep common English words like 'app', 'website', 'computer', 'internet' in English.",
    "ta": "Mix Tamil with English technical terms naturally. Use English for modern technology words.",
    "te": "Use Tenglish mixing pattern. Technical terms can stay in English.",
    "ml": "Manglish is common for tech content. Mix naturally."
}
```

---

### **Approach 5: Seasonal & Temporal References** (TIME-AWARE)

Make references time-aware based on current season/festivals:

```python
import datetime

def get_seasonal_context(language_code: str, month: int) -> str:
    """Get seasonal references based on current month"""
    
    SEASONAL_REFERENCES = {
        "hi": {
            10: "Diwali preparations, festive shopping season",  # October
            11: "Winter ki shuruaat, wedding season",           # November
            3: "Holi celebrations, spring season",              # March
            6: "Monsoon season, barish aur garmi",             # June
        },
        "ta": {
            1: "Pongal festival, harvest season",              # January
            4: "Tamil New Year, summer vacation",              # April
            8: "Aadi month, temple festivals",                 # August
        }
    }
    
    current_month = datetime.datetime.now().month
    return SEASONAL_REFERENCES.get(language_code, {}).get(current_month, "")
```

---

## 📊 Impact Comparison

### **Without Regional References:**
```
Teaching Script for "Database Indexing":
"Database indexing is like a book index. Just as you look up page numbers 
in an index to find topics quickly, databases use indexes to find data faster 
instead of searching through all records."
```

### **With Regional References (Hindi/Delhi):**
```
Teaching Script for "Database Indexing":
"Database indexing ko samajhne ke liye, Delhi Metro ka example lete hain. 
Jaise Metro map mein aap ek baar mein dekh lete ho ki Connaught Place jaane 
ke liye Yellow Line se Blue Line par switch karna hai, waise hi database index 
bhi ek map ki tarah kaam karta hai. Bina index ke, computer ko poora data 
check karna padta hai - jaise agar Metro map na ho toh har station par jaake 
poochhna padega. Lekin index se, turant pata chal jata hai data kahan hai. 
Flipkart jab crores of products mein se aapka search result 1 second mein 
dikhata hai, toh woh indexing ki wajah se hi possible hota hai."
```

**Improvement:**
- ✅ Uses familiar landmark (Connaught Place)
- ✅ Relatable daily experience (Delhi Metro)
- ✅ Local business example (Flipkart)
- ✅ Natural code-mixing (Hindi + English tech terms)
- ✅ Scale context (crores, not millions)

---

## 🔧 Implementation Checklist

### **Phase 1: Basic Regional Context** ✅ DONE
- [x] Create language-to-region mapping
- [x] Add regional context to LLM prompts
- [x] Test with different languages

### **Phase 2: Domain-Specific Examples** 🚧 NEXT
- [ ] Create domain detection logic
- [ ] Build domain-specific example mappings
- [ ] Test domain relevance

### **Phase 3: Advanced Personalization** 🔮 FUTURE
- [ ] Add city-specific targeting
- [ ] Implement seasonal references
- [ ] Add code-mixing guidelines
- [ ] User feedback loop for example quality

---

## 🎓 Best Practices

### **DO:**
✅ Use **specific** landmarks and businesses, not generic ones  
✅ Mix languages **naturally** as people actually speak  
✅ Choose examples that are **universally known** in that region  
✅ Keep references **positive** and culturally sensitive  
✅ Update examples **periodically** to stay current

### **DON'T:**
❌ Use controversial political or religious examples  
❌ Assume everyone knows very local/niche references  
❌ Force regional references where they don't fit naturally  
❌ Use outdated references (e.g., closed landmarks)  
❌ Mix multiple regions in one example (confusing)

---

## 🧪 Testing Regional References

**Test different topics with regional context:**

```python
# Example test cases
test_cases = [
    {
        "topic": "Cloud Computing",
        "language": "hi",
        "expected_references": ["Indian Railways", "Delhi Metro", "UPI payments"]
    },
    {
        "topic": "Supply Chain Management",
        "language": "ta",
        "expected_references": ["Chennai Port", "Tirupur textiles", "Coimbatore manufacturing"]
    },
    {
        "topic": "Machine Learning",
        "language": "mr",
        "expected_references": ["Mumbai Dabbawalas", "Traffic prediction", "Stock market"]
    }
]
```

---

## 📈 Measuring Success

**Metrics to track:**
1. **User Engagement**: Do users listen to complete narrations?
2. **Comprehension**: Do regional examples improve understanding? (surveys)
3. **Retention**: Do users remember content better with local context?
4. **Feedback**: Explicit ratings on example relevance

---

## 🌟 Advanced: Multi-Regional Content

For presentations targeting **multiple regions** (e.g., pan-India training):

```python
def generate_inclusive_examples(language_code: str, topic: str) -> List[str]:
    """Generate examples from multiple regions to be inclusive"""
    all_regions = ["North", "South", "East", "West"]
    examples = []
    
    for region in all_regions:
        regional_example = get_example_for_region(region, topic)
        examples.append(regional_example)
    
    return examples
```

**Example output:**
> "Network effects ko samajhne ke liye India ke alag-alag examples le sakte hain. 
> North mein Delhi Metro ka expansion, South mein Bangalore ke tech startups, 
> East mein Kolkata ke traditional business networks, aur West mein Mumbai ke 
> Dabbawalas - sabhi mein network effect ki power dikhti hai."

---

**This system makes AI-generated content feel personal, relatable, and culturally aware! 🎯**
