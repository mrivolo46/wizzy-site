---
title: "Cities in Wizzy"
description: "Every city in Wizzy, with the stories behind its landmarks."
permalink: /cities/
---

# {{ site.data.wizzy.city_count }} cities, {{ site.data.wizzy.landmark_count_text }} places

Pick a city to see its must-sees. The full set of stories, and the pings as you walk, are in the app.

<div class="wz-countries">
{% for country in site.data.wizzy.countries %}
<h2>{{ country.name }}</h2>
<p>{% for c in country.cities %}<a href="{{ '/cities/' | append: c.id | append: '/' | relative_url }}">{{ c.name }}</a>{% unless forloop.last %} · {% endunless %}{% endfor %}</p>
{% endfor %}
</div>

<p class="wz-cta">{% include appstore-badge.html ct="web-cities" %}</p>
