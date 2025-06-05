---
layout: page
title: people
permalink: /people/
description: our team
nav: true
nav_order: 3
display_categories: [principal investigator, postdocs, graduate researchers, undergraduate researchers, alumni]
horizontal: false
---

<!-- pages/projects.md -->
<div class="projects">
{% if site.enable_project_categories and page.display_categories %}
  <!-- Display categorized projects -->
  {% for category in page.display_categories %}
  <a id="{{ category }}" href=".#{{ category }}">
    <h2 class="category">{{ category }}</h2>
  </a>
  {% assign categorized_projects = site.projects | where: "category", category %}
  {% assign sorted_projects = categorized_projects | sort: "importance" %}
  <!-- Generate cards for each project -->
  {% if page.horizontal %}
  <div class="container">
    <div class="row row-cols-1 row-cols-md-2">
    {% for project in sorted_projects %}
      {% include projects_horizontal.liquid %}
    {% endfor %}
    </div>
  </div>
  {% else %}
  <div class="row row-cols-1 row-cols-md-3">
    {% for project in sorted_projects %}
      {% include projects.liquid %}
    {% endfor %}
  </div>
  {% endif %}
  {% endfor %}

{% else %}

<!-- Display projects without categories -->

{% assign sorted_projects = site.projects | sort: "importance" %}

  <!-- Generate cards for each project -->

{% if page.horizontal %}

  <div class="container">
    <div class="row row-cols-1 row-cols-md-2">
    {% for project in sorted_projects %}
      {% include projects_horizontal.liquid %}
    {% endfor %}
    </div>
  </div>
  {% else %}
  <div class="row row-cols-1 row-cols-md-3">
    {% for project in sorted_projects %}
      {% include projects.liquid %}
    {% endfor %}
  </div>
  {% endif %}
{% endif %}
</div>


<div class="projects">
  <!-- Display categorized projects -->
  <a id=past>
    <h2 class="category">past members</h2>
  </a>
</div>

## Undergraduate researchers

- Skyler DeVaughn (Software Engineering)
- Carter Pettid (Computer Science, Statistics)
- Nimet Beyza Bozdag (Computer Science, Mathematics)
- Tugay Bilgis (Computer Science, Mathematics)
- Thompson Nguyen (Computer Science)

## Short-term graduate researchers

- Saege Hagerty (Materials Science & Engineering)
- Aditya Jain (Management & Information Systems)
- Hao Qin (Statistics & Data Science)
- Eric Chirtel (Applied Math)
- Akshita Sharma (Applied Math)

## Visitors

- Gyu-Jang Sim (Seoul National University)