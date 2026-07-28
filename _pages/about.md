---
permalink: /
title: ""
author_profile: true
redirect_from: 
  - /about/
  - /about.html
---

<style type="text/css">
    h2 {text-align: left}
	h3 {text-align: left}
</style>

<style type="text/css">
	.someClass {
		display: flex;
		justify-content: space-between;
	}

	.content-container {
      display: flex;
      align-items: left;
      gap: 10px; /* 设置元素之间的间距 */
      flex-wrap: wrap; /* 如果屏幕过窄，元素会自动换行 */
    }

    .button-container {
      position: relative;
      display: inline-block;
    }

	/* Tooltip styling */
    .tooltip {
      visibility: hidden;
      background-color: #333;
      color: #fff;
      text-align: left;
      border-radius: 5px;
      padding: 5px;
      position: absolute;
      z-index: 1;
      bottom: 125%; /* Position above the button */
      left: 50%;
      transform: translateX(-50%);
      white-space: nowrap;
      font-size: 14px;
      opacity: 0;
      transition: opacity 0.3s;
    }

    /* Tooltip arrow */
    .tooltip::after {
      content: "";
      position: absolute;
      top: 100%; /* Position below the tooltip */
      left: 50%;
      transform: translateX(-50%);
      border-width: 5px;
      border-style: solid;
      border-color: #333 transparent transparent transparent;
    }

    /* Show tooltip on hover */
    .button-container:hover .tooltip {
      visibility: visible;
      opacity: 1;
    }

    /* Reusable layout for Education and Internship entries */
    .experience-item {
      display: flex;
      align-items: flex-start;
      gap: 24px;
      margin-bottom: 28px;
    }

    /* Every logo uses the same display box, regardless of source dimensions */
    .experience-logo {
      width: 170px;
      height: 90px;
      flex: 0 0 170px;
      display: flex;
      align-items: center;
      justify-content: center;
      overflow: hidden;
    }

    .experience-logo img {
      width: 140px;
      height: 80px;
      object-fit: contain;
      display: block;
      margin: 0;
      max-width: none;
      max-height: none;
    }

    .experience-details {
      flex: 1;
      min-width: 0;
    }

    .experience-details > p {
      margin: 0 0 8px 0;
    }

    .experience-details > ul {
      margin: 0;
      padding-left: 20px;
    }

    /* Keep the layout readable on narrow screens */
    @media (max-width: 600px) {
      .experience-item {
        gap: 14px;
      }

      .experience-logo {
        width: 110px;
        height: 72px;
        flex-basis: 110px;
      }

      .experience-logo img {
        width: 100px;
        height: 62px;
      }
    }
</style>

<script>
function refreshPage() {
      location.reload();
    }
</script>


<div class="content-container" style="font-size:0.8em;">
<!-- <img src="https://img.shields.io/github/actions/workflow/status/MicroSashimi/MicroSashimi.github.io/google_citation.yml?branch=main&logo=github" height="50px"> -->
<img src="https://img.shields.io/github/last-commit/MicroSashimi/MicroSashimi.github.io?logo=github" height="50px">
<!-- <img src="https://hits.seeyoufarm.com/api/count/incr/badge.svg?url=https%3A%2F%2FSashimi-Balls.github.io&count_bg=%2379C83D&title_bg=%23555555&icon=googleanalytics.svg&icon_color=%23E7E7E7&title=visits&edge_flat=false" height="50px"/> -->
<div class="button-container">
      <button class="refresh-btn" onclick="refreshPage()">Refresh</button>
      <div class="tooltip">Refresh for Updates</div>
</div>
<!-- <button class="refresh-btn" onclick="refreshPage()" height="50px">Refresh</button><div class="tooltip">Click to refresh the page</div> -->
</div>
<br>

Hi! Thanks for visiting my homepage!  

I am Yushen Wang, an incoming Master student at [**Shanghai Jiao Tong University**](https://www.sjtu.edu.cn/). I received my Bachelor of Engineering (B.Eng.) degree in *Communication Engineering* at [**University of Electronic Science and Technology of China (UESTC)**](https://www.uestc.edu.cn/) in June 2026. I am interested in broad areas related to LLMs and have been constantly exploring emerging topics.

My current research focuses on **memory-augmented LLMs**. Feel free to contact me if necessary!   

<b><a href="/files/CV_YushenWang.pdf" ><font color="#000000">Download Full CV</font></a></b>


<h2 id="research-interests">🔬 Research Interests</h2>

- 🤖 **Memory foundation models**: how to internalize native memory capability to foundation models?

<div style="display: flex; align-items: left;">
	<img src="../images/Metis_framework.png" alt="UESTC_banner" style="width: 70%;">
</div>

- 🧠 **LLM reasoning**: how to facilitate logical reasoning of LLMs?

- 📹 **Image processing and video streaming**: e.g., efficient and lossless video compression



<h2 id="publications">📚 Publications</h2>

Only list selected publications. <a href="/publications/">[Click here to see more details]</a>

### Journals

<ol class="publications">
{% assign sorted_pubs = site.publications | where: "type", "Journal" | sort: 'date' | reverse %}
{% for pub in sorted_pubs %}
	{% if pub.type == "Journal" %}
	<p style="text-indent: -1.5rem;margin-left: 0rem;">
	<span class="publications-number">[{{ sorted_pubs.size | minus: forloop.index | plus: 1  }}]</span>
	{% assign authors = pub.authors | split: ", " %}
	{% for author in authors %}
		{% if author == "Y. Wang" %}
			<strong>{{ author }}</strong>{% if forloop.last == false %}, {% endif %}
		{% elsif author == "W. Mei" %}
			<i>{{ author }}*</i>{% if forloop.last == false %}, {% endif %}
		{% else %}
		  	{{ author }}{% if forloop.last == false %}, {% endif %}
		{% endif %}
	{% endfor %}
	, "{{ pub.title }}", <i>{{ pub.venue }}</i>, vol. {{ pub.vol }}, no. {{ pub.issue }}, pp. {{ pub.pp }}, {{ pub.date | date: "%b. %Y" }}.
	{% if pub.arxiv %}
		[<a href="{{ pub.arxiv }}" target="_blank">arXiv</a>]
	{% endif %}
	{% if pub.slidesurl %}
		[<a href="{{ pub.slidesurl }}" target="_blank">Slides</a>]
	{% endif %}
	{% if pub.paperurl %}
		[<a href="{{ pub.paperurl }}" target="_blank">Paper</a>]
	{% endif %}
	{% if pub.errata %}
		[<a href="{{ pub.errata }}" target="_blank">errata</a>]
	{% endif %}
	{% if pub.codes %}
		[<a href="{{ pub.codes }}" target="_blank"><font color="#FF0000">Codes</font></a>]
	{% endif %}
	{% if pub.DOI %}
		<a href="https://doi.org/{{ pub.DOI }}" target="_blank"><img src="https://zenodo.org/badge/DOI/{{ pub.DOI }}.svg" height="60px"></a>
		<img src="https://api.juleskreuer.eu/citation-badge.php?doi={{ pub.DOI }}" height="60px">
	{% endif %}
	<br>
  	</p>
	{% endif %}
{% endfor %}
</ol>

### Conferences
<ol class="publications">
{% assign sorted_pubs = site.publications | where: "type", "Conference" | sort: 'date' | reverse %}
{% for pub in sorted_pubs %}
	{% if pub.type == "Conference" %}
	<p style="text-indent: -1.5rem;margin-left: 0rem;">
    <span class="publications-number">[{{ sorted_pubs.size | minus: forloop.index | plus: 1  }}]</span>
    {% assign authors = pub.authors | split: ", " %}
    {% for author in authors %}
        {% if author == "Y. Wang" %}
        	<strong>{{ author }}</strong>{% if forloop.last == false %}, {% endif %}
		{% elsif author == "W. Mei" %}
			<i>{{ author }}*</i>{% if forloop.last == false %}, {% endif %}
        {% else %}
          	{{ author }}{% if forloop.last == false %}, {% endif %}
        {% endif %}
    {% endfor %}
    , "{{ pub.title }}",
	{% if pub.type == "Conference" %}
		in <i>{{ pub.venue }}</i>, {{ pub.location }}, {{ pub.date | date: "%b. %Y" }}.
	{% endif %}
	{% if pub.arxiv %}
		[<a href="{{ pub.arxiv }}" target="_blank">arXiv</a>]
	{% endif %}
	{% if pub.slidesurl %}
		[<a href="{{ pub.slidesurl }}" target="_blank">Slides</a>]
	{% endif %}
	{% if pub.paperurl %}
		[<a href="{{ pub.paperurl }}" target="_blank">Paper</a>]
	{% endif %}
	{% if pub.codes %}
		[<a href="{{ pub.codes }}" target="_blank"><font color="#FF0000">Codes</font></a>]
	{% endif %}
	{% if pub.DOI %}
		<a href="https://doi.org/{{ pub.DOI }}" target="_blank"><img src="https://zenodo.org/badge/DOI/{{ pub.DOI }}.svg" height="60px"></a>
		<img src="https://api.juleskreuer.eu/citation-badge.php?doi={{ pub.DOI }}" height="60px">
	{% endif %}
	<br>
  	</p>
	{% endif %}
{% endfor %}
</ol>


<h2 id="honors">🎉 Honors</h2>

- <b><font color="#000000">[2023.12]</font></b> Corporate Scholarship, Luzhou Laojiao
- <b><font color="#000000">[2023.12]</font></b> Outstanding Student Scholarship, UESTC
- <b><font color="#000000">[2024.12]</font></b> <font color="#FF0000">National Scholarship</font> for Undergraduates, Chinese Ministry of Education
- <b><font color="#000000">[2024.12]</font></b> Outstanding Student Scholarship, UESTC
- <b><font color="#000000">[2025.11]</font></b> Outstanding Graduate of Sichuan Province, Sichuan Provincial Department of Education


<h2 id="awards">🏆 Awards</h2>
- <b><font color="#000000">[2024.02]</font></b> Honorable Mention, Mathematical Contest in Modeling
- <b><font color="#000000">[2024.05]</font></b> National Third Prize, National English Competition for College Students


<h2 id="services">✍️ Services</h2>

- **Peer Reviewer**, IEEE ICC Workshop'25, Montreal, Canada.


<h2 id="internship">💼 Internship</h2>

<div class="experience-item">
    <div class="experience-logo">
        <img src="/images/memtensor_logo.jpeg" alt="Internship company logo">
    </div>
    <div class="experience-details">
        <p><strong>MemTensor</strong></p>
        <ul>
            <li>LLM Algorithm Intern, Jun. 2026 - Present</li>
            <li>Research focus: memory foundation models</li>
        </ul>
    </div>
</div>


<h2 id="education">🎓 Education</h2>

<div class="experience-item">
    <div class="experience-logo">
        <img src="/images/UESTC.png"
             alt="University of Electronic Science and Technology of China logo">
    </div>
    <div class="experience-details">
        <p><strong>University of Electronic Science and Technology of China</strong></p>
        <ul>
            <li>B.Eng. in Communication Engineering, Sept. 2022 - Jun. 2026</li>
            <li>Supervisor: <a href="https://faculty.uestc.edu.cn/meiweidong/zh_CN/index.htm">Prof. Weidong Mei</a></li>
        </ul>
    </div>
</div>

<div class="experience-item">
    <div class="experience-logo">
        <img src="/images/SJTU.png"
             class="logo-sjtu"
             alt="Shanghai Jiao Tong University logo">
    </div>
    <div class="experience-details">
        <p><strong>Shanghai Jiao Tong University</strong></p>
        <ul>
            <li>M.Eng. in Information and Communication Engineering, Sept. 2026 - Jun. 2029 (expected)</li>
        </ul>
    </div>
</div>
