# QA Guide for Xio

Hey Xio! Thank you for taking this on. Here's everything you need to know to start
reviewing Whappin Puerto Viejo.

---

## Your Tools

You only need two things:

1. **A browser** — go to https://www.whappin.com/
2. **A GitHub account** — create one free at github.com/signup, then you're set

That's it. No special software, no admin panel, no spreadsheets.

---

## How QA Works (the simple version)

1. Browse the site
2. Find something wrong or worth improving
3. Click **"Report a problem"** in the footer of any page
4. Fill in the form and submit
5. It creates a GitHub issue — Oscar and I see it immediately
6. We fix the data or code and deploy the change

That's the whole loop. You file issues, we make fixes.

---

## What to Look For

### Priority 1 — Wrong or missing data

These are the most important things to catch:

| What to check | How to spot it | Example issue |
|---------------|----------------|--------------|
| Closed businesses still listed | The page shows contact buttons but the business is permanently closed | "El Faro 13 is closed — remove contact buttons" |
| Wrong phone number | Call the number and it's not the business | "Selvin's Restaurant phone number is wrong" |
| Wrong WhatsApp number | The WhatsApp link goes to the wrong person | "Caribe Horse Riding WhatsApp is incorrect" |
| Wrong business name | The listing name doesn't match the real sign | "Casa Alegra and Casa Alegre are the same place" |
| Wrong category | A hotel listed as restaurant, etc. | "Tasty Waves Cantina is a restaurant, not a hotel" |
| Duplicate entries | Same business listed twice under different names | "Casa Miluca and Casa Miluco are duplicates" |

### Priority 2 — Missing information

These make a listing less useful:

- No website link when the business has one
- No Instagram handle when you can find one
- No phone number when you can find one
- No description (shows auto-generated text)
- No amenities shown (nothing in the Amenities section)
- No star rating

### Priority 3 — Presentation issues

These are polish items:

- Photos look wrong or distorted
- Text is cut off or garbled
- Buttons don't work as expected
- Something doesn't make sense on mobile vs desktop
- The map doesn't show the right location
- The QR code doesn't scan to the right page

---

## How to File a Good Bug Report

When you click "Report a problem" in the footer, you'll get a form with these fields:

**What were you doing?**
Example: "I was looking at Selvin's Restaurant to see if they have a website."

**What happened?**
Example: "The website link goes to the wrong URL — it shows a hotel booking site instead."

**What did you expect?**
Example: "I expected it to go to selvinspuertoviejo.com."

**Where?**
Paste the page URL from your browser address bar.
Example: https://www.whappin.com/businesses/selvin-s-restaurant-and-cabinas-playa-punta-uva-puerto-viejo-lim-n-costa-rica-pu.html

**Device / Browser:**
Just say "Desktop" or "Phone" and which browser (Chrome, Safari, etc.)

**How bad is it?**
Pick one:
- **Broken** — can't use this feature at all
- **Wrong** — data or behavior is incorrect
- **Confusing** — had to think about what to do
- **Polish** — looks off but works
- **Idea** — would be nice to have

---

## What to Review First

Start here, in this order. Each section has ~20-30 businesses.

### Batch 1: Restaurants with thin data (highest impact for visitors)

These are restaurants that have no amenities listed and may have auto-generated
descriptions. Search for these in the app:

```
Abba Home, Api-Rescate, Beach Trail, Buddy's Sloth Crossing,
Cafe Jaguar & Art Gallery, Casa Alegra, Casa Chilamate Day House,
Cirrus Sky Paragliding CR, Cubali Beach, Explora Caribe CR,
Gigi O Restaurant, Hidden Viewpoint, Izzy Rides CR, Jungalow,
Katuk, La Caracola, Lapaluna, Nana's Place Beach House,
NAO, Paraiso Bohemio, Pipa's Beach, Playa Estiven,
RETIRO VERDE, Rico Tico Tours, River Box Cocles, Siren Sanctuary,
Spiral, Talamanca Viewpoint, Tasty Waves Cantina, Watuza
```

For each one, check:
- Does the description make sense?
- Does it have contact info (phone, Instagram, website)?
- Does it have any amenities listed?
- Is the category right?

### Batch 2: Hotels without amenity data

Search for "Hotel" in the app and look for ones with few or no amenities.

### Batch 3: The 23 "needs_verification" records

These are flagged as needing verification:

```
Watuza, El Faro 13, Hotel Los Sueños, Villa Buké, Beach Hut,
Mi Casa Hostel y Hotel El Tesoro, Cabinas Orange Green, Cabinas Wray,
Casa Badawi, Casa Trinidad, Casa Tuareg, Harmony Mini Casa Rodante,
Hotel Posada Nada, Las Mariposas, Paula's and Daniel's Homestay,
Vista Verde, Restaurante Cariblue, Río Negro, Jungle Air Parapente,
Panadería Francés, Hotel Villas y Glamping M&A,
Yerbas Concepto Culinario, Casa Miluca
```

### Batch 4: Anything that catches your eye

Browse naturally — search for places you know, look at categories you're
interested in, follow your curiosity.

---

## What Happens After You File an Issue

1. Your issue appears on GitHub with a `qa` label
2. Oscar or I review it
3. If it's a data fix (wrong phone, wrong category, etc.), I edit the CSV
   and deploy — typically within minutes
4. If it's a code fix (something broken in the page layout, a button
   not working), I fix and deploy — usually within an hour
5. You'll get a notification when the issue is closed

---

## Don't Worry About

- **Breaking anything.** You can't — you're filing issues, not editing code.
- **Being too picky.** If you notice it, it's worth flagging.
- **Not knowing GitHub.** The form is simple — just fill in the fields.
- **Having the right answer.** If you're not sure, file it anyway with
  "Not sure but..." and we'll figure it out.

---

## The One Thing That Helps Most

**Mention the business name and the page URL in every issue.** That way we
can find and fix it immediately without having to ask "which one?"

---

Thank you, Xio. Every issue you file makes the site better for everyone
in Puerto Viejo.

— The Whappin team
