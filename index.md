---
title: Wizzy
---

<div class="wz-hero">
  <img class="wz-icon" src="{{ '/assets/icon.png' | relative_url }}" alt="Wizzy app icon">
  <h1>Wizzy</h1>
  <p class="wz-tagline">Just walk. Wizzy tells you what you're passing.</p>
  {% include appstore-badge.html ct="web-home" %}
</div>

Wizzy is an iPhone app with short stories about the landmarks around you, and a tap on the shoulder when you walk past one. No tour to follow, no audio to keep up with: start a walk, put your phone away, and Wizzy pings you when there's something worth looking up at.

<div class="wz-screens">
  <img src="{{ '/assets/screens/map.jpg' | relative_url }}" alt="Map of landmarks around you">
  <img src="{{ '/assets/screens/story.jpg' | relative_url }}" alt="A short story about a landmark">
  <img src="{{ '/assets/screens/route.jpg' | relative_url }}" alt="A planned walking route">
  <img src="{{ '/assets/screens/walks.jpg' | relative_url }}" alt="Your walk journal">
  <img src="{{ '/assets/screens/passport.jpg' | relative_url }}" alt="Your passport, with a stamp for each city">
</div>

## What it does

- **Pings as you walk.** Start a walk and Wizzy taps you on the shoulder when you pass a landmark, even with your phone locked.
- **Stories, not encyclopedia entries.** Every place gets a short story you can read in the time it takes to cross the street.
- **Plan a route or just wander.** Build a walk from the map, or start walking and let the city surprise you.
- **Keep a journal.** Every walk is saved as a day with a map of where you went.
- **Fill your passport.** Each city you explore gets a stamp that fills in as you see its landmarks.
- **Travel together.** Make a group, invite friends with a link, see how much of the city each of you has seen, and share a trip album.
- **Private by design.** Your location stays on your phone. No ads, no analytics.

## {{ site.data.wizzy.city_count }} cities, {{ site.data.wizzy.landmark_count_text }} landmarks

<ul class="wz-cities">
{%- for c in site.data.wizzy.cities %}
  <li><a href="{{ '/cities/' | append: c.id | append: '/' | relative_url }}">{{ c.name }}</a></li>
{%- endfor %}
</ul>

[See every city by country](cities/)

<p style="text-align:center;margin-top:2rem">
  {% include appstore-badge.html ct="web-home" %}
</p>

---

[Support](support/) · [Privacy Policy](privacy/)
