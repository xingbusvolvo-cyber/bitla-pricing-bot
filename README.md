# Bitla Pricing Bot - Setup Guide (Step by Step)

Ye guide bilkul simple bhasha mein hai. Koi coding knowledge nahi chahiye,
bas copy-paste karna hai.

## Cheezein jo pehle se ban chuki hain
- Claude (Anthropic) API Key ✅
- Telegram Bot Token ✅
- Railway.app account ✅

## Step 1: GitHub par code upload karna

1. github.com par jao, agar account nahi hai to bana lo (free hai)
2. Login karne ke baad, top-right corner mein **"+"** icon dabao, phir
   **"New repository"** select karo
3. Repository ka naam do: `bitla-pricing-bot`
4. **"Public"** ya **"Private"** - dono chalega, Private zyada safe hai
5. **"Create repository"** dabao
6. Us naye khaali page par **"uploading an existing file"** link milegi -
   us par click karo
7. Is folder ki saari files (jo aapko di gayi hain) yahan drag-drop karo
   ya "choose your files" se select karo
8. Neeche **"Commit changes"** button dabao

## Step 2: Railway ko GitHub se jodna

1. railway.app par jao, apne account mein login karo
2. **"New Project"** dabao
3. **"GitHub Repository"** select karo
4. Apni `bitla-pricing-bot` repository dhundo aur select karo
5. Railway khud detect kar lega ke ye Python project hai aur build shuru
   kar dega (thoda time lagega, 2-5 minute)

## Step 3: Secret keys Railway mein daalna

1. Railway dashboard mein apne project par click karo
2. **"Variables"** tab dhundo (ya "Settings" ke andar)
3. Ye 3 variables add karo (Name aur Value dono daalne honge):

   | Name | Value |
   |------|-------|
   | ANTHROPIC_API_KEY | (wo lambi si key jo Claude console se mili thi) |
   | TELEGRAM_BOT_TOKEN | (wo token jo BotFather ne diya) |
   | TELEGRAM_CHAT_ID | (neeche Step 4 mein batayenge kaise nikalna hai) |

## Step 4: Apna Telegram chat_id nikalna

1. Telegram kholo, apna bot dhundo (jo username diya tha, jaise
   `@bitla_pricing_bot`) aur usay ek message bhejo, sirf "hi" likh do
2. Ab Railway dashboard mein jao, project ke andar **"Settings" → "Deploy"**
   mein ek tarika hota hai one-off command chalane ka - agar wo mushkil
   lage, seedha browser mein ye link kholo (apna asli token daal ke):

   ```
   https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/getUpdates
   ```

   Jaise agar token hai `123456:ABC...`, to link hoga:
   `https://api.telegram.org/bot123456:ABC.../getUpdates`

3. Is page par ek JSON dikhega, usme `"chat":{"id":XXXXXXX` jaisa kuch
   likha milega - wahi number hai aapka **chat_id**
4. Wapas Railway Variables mein jaake `TELEGRAM_CHAT_ID` mein ye number
   daal do

## Step 5: Anthropic account mein credits daalna

Agar abhi tak nahi daale, console.anthropic.com > Billing > Add funds se
$10-20 daal do. Bina isके bot chalega lekin Claude recommendation nahi
de payega.

## Step 6: Deploy check karna

1. Railway mein Variables save karne ke baad, project apne aap **redeploy**
   hoga (2-3 minute)
2. Deploy complete hote hi, Telegram par bot se aapko message aana chahiye:
   "🤖 Bitla Pricing Bot online ho gaya hai." - agar ye aa gaya, sab sahi
   chal raha hai!
3. Uske turant baad pehla pricing-check bhi aa jayega (kyunke code startup
   par ek baar turant chalta hai)

## Roz kya hoga

Bot din mein 3 baar (subah 9, dopeher 2, shaam 7 - IST) khud check karega
aur Telegram par message bhejega jaisa:

```
📍 Delhi to Manali (Semi Sleeper)
Current: ₹800 🔺 Suggested: ₹950
Reason: Weekend hai aur demand zyada dikh rahi hai.
```

Aapko bas ye number dekh kar Bitla/TicketSimply dashboard mein manually
update karna hai.

## Agar kuch kaam na kare

- **Message nahi aa raha**: TELEGRAM_CHAT_ID sahi hai check karo
- **"Data analyze nahi ho paya" wala reason aa raha ho**: Claude credits
  khatam ho gaye ya key galat hai - console.anthropic.com check karo
- **Scraping fail ho rahi ho baar baar**: RedBus ne apni website ki
  design change kar di hai - scraper.py file mein selectors update
  karne honge (ye wapas Claude se madad le kar theek karwaya ja sakta hai)

## Fare range badalna

`config.py` file mein `MIN_FARE_PERCENT` aur `MAX_FARE_PERCENT` change
karke aap decide kar sakte ho ke fare current price se kitna neeche/upar
ja sakti hai. Naya route add karna ho to `ROUTES` list mein ek aur entry
add kar do, same format follow karte hue.
