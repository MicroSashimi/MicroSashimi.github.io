---
layout: archive
title: "Sitemap"
permalink: /sitemap/
author_profile: true
---

{% include base_path %}

{% if site.author.googlescholar %}

<div class="wordwrap">
  You can also find my articles on
  <a href="{{ site.author.googlescholar }}" target="_blank" rel="noopener">
    my Google Scholar profile
  </a>.
</div>
{% endif %}

{% assign sorted_publications = site.publications | sort: "date" | reverse %}

{% if sorted_publications.size > 0 %}{% for post in sorted_publications %}

  <article class="archive__item" itemscope itemtype="https://schema.org/ScholarlyArticle"
           style="margin-bottom: 2.2rem;">

<h2 class="archive__item-title" itemprop="headline" style="margin-bottom: 0.45rem;">
  <a href="{{ base_path }}{{ post.url }}" rel="permalink">
    {{ post.title }}
  </a>
</h2>

{% if post.authors %}
<p style="margin: 0.25rem 0;">
  <strong>Authors:</strong> {{ post.authors }}
</p>
{% endif %}

<p style="margin: 0.25rem 0;">
  {% if post.type %}
    <strong>Type:</strong> {{ post.type }}
  {% endif %}
  {% if post.venue %}
    {% if post.type %}<br>{% endif %}
    <strong>Venue:</strong> <i>{{ post.venue }}</i>
  {% endif %}
  {% if post.date %}
    <br><strong>Date:</strong> {{ post.date }}
  {% endif %}
  {% if post.location %}
    <br><strong>Location:</strong> {{ post.location }}
  {% endif %}
</p>

{% if post.excerpt %}
<div class="archive__item-excerpt" itemprop="description">
  {{ post.excerpt | markdownify }}
</div>
{% endif %}

<p style="margin-top: 0.6rem;">
  {% if post.paperurl %}
    [<a href="{{ post.paperurl }}" target="_blank" rel="noopener">Paper</a>]
  {% endif %}
  {% if post.arxiv %}
    [<a href="{{ post.arxiv }}" target="_blank" rel="noopener">arXiv</a>]
  {% endif %}
  {% if post.codes %}
    [<a href="{{ post.codes }}" target="_blank" rel="noopener">Code</a>]
  {% endif %}
  {% if post.slidesurl %}
    [<a href="{{ post.slidesurl }}" target="_blank" rel="noopener">Slides</a>]
  {% endif %}
  [<a href="{{ base_path }}{{ post.url }}">Details</a>]
</p>

  </article>
  {% endfor %}
{% else %}
  <p>No publications are available yet.</p>
{% endif %}
