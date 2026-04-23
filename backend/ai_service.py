try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Gemini not available - using fallback responses")

# 🔴 Replace with your actual Gemini API key
GEMINI_API_KEY = 'AIzaSyC-SHiUTiFkLNaVtSE4TWfY51vSuwCholo'

SYSTEM_PROMPT = """
You are DisasterBot, an AI assistant specialized in
disaster preparedness and emergency response education.

You help students and teachers with:
1. Earthquake safety and preparedness
2. Flood safety and evacuation
3. Fire safety and prevention
4. Cyclone preparedness
5. First aid and emergency response
6. Evacuation routes and procedures
7. Emergency kit preparation
8. Disaster recovery tips

Rules:
- Only answer questions related to disaster preparedness
- Give clear simple actionable advice
- Always mention emergency numbers when relevant
  112 Emergency, 101 Fire, 102 Ambulance, 100 Police
- Be encouraging and calm
- Keep responses concise and easy to understand
- If asked about unrelated topics politely redirect
  to disaster safety topics
"""

def get_ai_response(user_message, chat_history=[]):
    # Try Gemini API first
    if GEMINI_AVAILABLE and GEMINI_API_KEY != 'AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx':
        try:
            client = genai.Client(api_key=GEMINI_API_KEY)

            # Build conversation
            context = SYSTEM_PROMPT + "\n\nConversation:\n"
            for msg in chat_history[-6:]:
                role = "User" if msg['role'] == 'user' else "DisasterBot"
                context += f"{role}: {msg['content']}\n"
            context += f"\nUser: {user_message}\nDisasterBot:"

            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=context
            )

            return {
                'success': True,
                'message': response.text
            }
        except Exception as e:
            print(f"Gemini API error: {e}")

    # Fallback responses when API not available
    return {
        'success': True,
        'message': get_fallback_response(user_message)
    }


def get_fallback_response(message):
    message_lower = message.lower()

    if any(word in message_lower for word in
           ['earthquake', 'quake', 'tremor', 'seismic']):
        return """🌍 **Earthquake Safety Tips:**

- **DROP** to your hands and knees immediately
- **COVER** under a sturdy table or desk
- **HOLD ON** until shaking completely stops
- Stay away from windows and outside walls
- If outdoors move away from buildings and power lines
- After shaking stops check for injuries carefully
- Be prepared for aftershocks

⚠️ Emergency: **112** | Fire: **101** | Ambulance: **102**"""

    elif any(word in message_lower for word in
             ['flood', 'water', 'rain', 'inundation', 'flash']):
        return """🌊 **Flood Safety Tips:**

- Move to **higher ground immediately**
- Never walk through moving flood water
- Just 6 inches of water can knock you down
- Disconnect all electrical appliances
- Take emergency kit and important documents
- Follow official evacuation routes only
- Do not drive through flooded roads

⚠️ Emergency: **112** | Stay safe!"""

    elif any(word in message_lower for word in
             ['fire', 'smoke', 'burn', 'flame', 'blaze']):
        return """🔥 **Fire Safety Tips:**

- **GET OUT** of the building immediately
- **STAY OUT** never go back inside
- **CALL 101** for fire emergency services
- Crawl low under smoke to escape
- Feel doors before opening them
- Stop Drop and Roll if clothes catch fire
- Meet at your family emergency meeting point

⚠️ Fire: **101** | Emergency: **112**"""

    elif any(word in message_lower for word in
             ['cyclone', 'hurricane', 'storm', 'typhoon', 'wind']):
        return """🌀 **Cyclone Safety Tips:**

- Stay **indoors** away from windows
- Board up windows and secure loose items
- Move to the **strongest part** of the building
- Listen to **emergency broadcasts** on radio
- Fill bathtubs with water for emergency use
- Wait for **official all clear** before going outside
- Keep emergency kit ready at all times

⚠️ Emergency: **112** | Disaster: **1070**"""

    elif any(word in message_lower for word in
             ['kit', 'prepare', 'supplies', 'emergency bag', 'go bag']):
        return """🎒 **Emergency Kit Essentials:**

- 💧 Water — 1 gallon per person per day (3 days)
- 🍱 Non-perishable food (3 day supply)
- 💊 First aid kit and prescription medicines
- 🔦 Flashlight and extra batteries
- 📱 Charged mobile phone and power bank
- 📄 Important documents in waterproof bag
- 💰 Cash and emergency contacts list
- 👕 Extra clothes and warm blanket
- 📻 Battery powered radio for updates
- 🔑 House and car keys

⚠️ Emergency: **112**"""

    elif any(word in message_lower for word in
             ['first aid', 'injury', 'hurt', 'wound',
              'bleed', 'burn', 'fracture']):
        return """🚑 **Basic First Aid Tips:**

- **Call 102** for ambulance immediately
- For bleeding — apply firm pressure with clean cloth
- Do NOT remove objects stuck in wounds
- For burns — cool with running water for 10 minutes
- Do NOT apply ice directly to burns
- Keep injured person calm and still
- Do NOT give food or water to unconscious person
- Learn CPR — it can save lives!

⚠️ Ambulance: **102** | Emergency: **112**"""

    elif any(word in message_lower for word in
             ['evacuate', 'evacuation', 'escape', 'route', 'shelter']):
        return """🗺️ **Evacuation Guidelines:**

- Know your evacuation routes BEFORE disaster strikes
- Have a family meeting point outside your home
- Take only essential items — do not delay!
- Help elderly and children evacuate first
- Follow instructions from local authorities
- Never return until official all clear is given
- Register at evacuation shelter when you arrive

⚠️ Emergency: **112** | Disaster: **1070**"""

    elif any(word in message_lower for word in
             ['number', 'contact', 'call', 'helpline', 'emergency']):
        return """📞 **Emergency Contact Numbers India:**

🔴 **112** — National Emergency Number
🔴 **101** — Fire Department
🔴 **102** — Ambulance Service
🔴 **100** — Police
🔴 **1070** — National Disaster Helpline
🔴 **1078** — Flood Relief
🔴 **108** — Emergency Medical Services

Save all these numbers in your phone right now!
Being prepared can save your life! 🛡️"""

    elif any(word in message_lower for word in
             ['hello', 'hi', 'hey', 'help', 'start', 'what can']):
        return """👋 Hello! I am **DisasterBot** — your AI disaster safety assistant!

I can help you with:
🌍 **Earthquake** safety and preparedness
🌊 **Flood** evacuation procedures
🔥 **Fire** prevention and escape
🌀 **Cyclone** safety measures
🚑 **First Aid** tips
🎒 **Emergency Kit** preparation
🗺️ **Evacuation** route guidance
📞 **Emergency Numbers**

Just ask me anything about disaster safety!
I am here to help you stay safe! 🛡️"""

    else:
        return """🤖 I am **DisasterBot** — specialized in disaster safety!

I can help you with these topics:
🌍 Earthquake safety
🌊 Flood evacuation
🔥 Fire prevention
🌀 Cyclone preparedness
🚑 First aid tips
🎒 Emergency kit preparation
📞 Emergency contact numbers

Please ask me a question about any of these topics
and I will give you detailed safety information!

⚠️ Emergency Numbers:
- General Emergency: **112**
- Fire: **101**
- Ambulance: **102**
- Police: **100**
- Disaster Helpline: **1070**"""