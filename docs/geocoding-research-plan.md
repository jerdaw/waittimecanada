# Hospital Data Research Plan

---

## Request Template

Create a CSV dataset of Ontario, Canada hospital locations.

**Output format required (CSV with header):**
```
hospital_name,city,address,latitude,longitude,phone
```

**Example output:**
```
hospital_name,city,address,latitude,longitude,phone
CHEO,Ottawa,401 Smyth Road,45.4014,-75.6515,613-737-7600
Toronto General Hospital,Toronto,200 Elizabeth Street,43.6591,-79.3886,416-340-4800
```

**Use these 154 Ontario hospitals as the input list:**

1. Alexandra Hospital
2. Alexandra Marine and General Hospital
3. Almonte General Hospital
4. Anson General Hospital
5. Arnprior Regional Health
6. Atikokan General Hospital
7. Bingham Memorial Hospital
8. Blanche River Health - Englehart
9. Blanche River Health - Kirkland
10. Bluewater Health - Charlotte Eleanor Englehart (Petrolia)
11. Bluewater Health - Sarnia General Site
12. Brant Community Healthcare System - Brantford
13. Brightshores Health System - Lions Head Site
14. Brightshores Health System - Markdale Site
15. Brightshores Health System - Meaford Site
16. Brightshores Health System - Owen Sound
17. Brightshores Health System - Southampton Site
18. Brightshores Health System - Wiarton Site
19. Brockville General Hospital
20. Cambridge Memorial Hospital
21. Campbellford Memorial Hospital
22. Carleton Place and District Memorial Hospital
23. Centre for Addiction and Mental Health - Queen Street Site
24. Chatham-Kent Health Alliance - Chatham
25. Chatham-Kent Health Alliance - Wallaceburg
26. CHEO (Children's Hospital of Eastern Ontario)
27. Collingwood General and Marine Hospital
28. Cornwall Community Hospital
29. Deep River and District Hospital
30. Dryden Regional Health Centre
31. Erie Shores Healthcare
32. Espanola General Hospital
33. Four Counties Health Services Corporation
34. Georgian Bay General Hospital - Midland Site
35. Glengarry Memorial Hospital
36. Grand River Hospital
37. Groves Memorial Community Hospital
38. Guelph General Hospital
39. Haldimand War Memorial Hospital
40. Haliburton Highlands Health Services - Haliburton
41. Halton Healthcare Services - Georgetown
42. Halton Healthcare Services - Milton
43. Halton Healthcare Services - Oakville
44. Hamilton Health Sciences
45. Hanover and District Hospital
46. Hawkesbury and District General Hospital
47. Headwaters Health Care Centre - Dufferin
48. Health Sciences North - Laurentian
49. Hopital Montfort
50. Hopital Notre Dame Hospital (Hearst)
51. Hospital for Sick Children (SickKids)
52. Humber River Health - Wilson Site
53. Huron Perth Healthcare Alliance - Clinton
54. Huron Perth Healthcare Alliance - Seaforth
55. Huron Perth Healthcare Alliance - St. Marys
56. Huron Perth Healthcare Alliance - Stratford
57. Joseph Brant Hospital
58. Kemptville District Hospital
59. Kingston Health Sciences Centre
60. Lake of the Woods District Hospital
61. Lakeridge Health - Ajax Site
62. Lakeridge Health - Bowmanville Site
63. Lakeridge Health - Oshawa Site
64. Lakeridge Health - Port Perry Site
65. Lennox and Addington County General Hospital
66. Listowel Memorial Hospital
67. London Health Sciences Centre - University Hospital
68. London Health Sciences Centre - Victoria Hospital
69. Mackenzie Health - Cortellucci Vaughan Hospital
70. Mackenzie Health - Jane Street Site
71. Mackenzie Health - Richmond Hill Hospital
72. Manitoulin Health Centre - Little Current
73. Manitoulin Health Centre - Mindemoya Unit
74. Manitouwadge General Hospital
75. Mattawa General Hospital
76. McCausland Hospital
77. Mount Sinai Hospital
78. Muskoka Algonquin Healthcare - Bracebridge
79. Muskoka Algonquin Healthcare - Huntsville
80. Niagara Health System - Fort Erie Douglas Site
81. Niagara Health System - Greater Niagara
82. Niagara Health System - Port Colborne Site
83. Niagara Health System - St. Catharines General
84. Niagara Health System - Welland County
85. Nipigon District Memorial Hospital
86. Norfolk General Hospital
87. North Bay Regional Health Centre
88. North Shore Health Network - Blind River Site
89. North Shore Health Network - Richards Landing
90. North Shore Health Network - Thessalon Site
91. North Wellington Health Care - Mount Forest
92. North Wellington Health Care - Palmerston
93. North York General Hospital
94. Northumberland Hills Hospital
95. Oak Valley Health - Markham Stouffville Hospital
96. Oak Valley Health - Uxbridge Hospital
97. Orillia Soldiers' Memorial Hospital
98. Ottawa Hospital - Civic Campus
99. Ottawa Hospital - General Campus
100. Pembroke Regional Hospital
101. Perth and Smiths Falls District Hospital - Perth Site
102. Perth and Smiths Falls District Hospital - Smiths Falls Site
103. Peterborough Regional Health Centre
104. Queensway Carleton Hospital
105. Quinte Health - Bancroft
106. Quinte Health - Belleville
107. Quinte Health - Picton
108. Quinte Health - Trenton
109. Renfrew Victoria Hospital
110. Riverside Health Care Facilities - La Verendrye
111. Riverside Health Care Facilities - Rainy River
112. Ross Memorial Hospital
113. Royal Victoria Regional Health Centre
114. Sault Area Hospital - Sault Ste. Marie
115. Scarborough Health Network
116. Sensenbrenner Hospital
117. Services de Sante de Chapleau Health Services
118. Sioux Lookout Meno Ya Win Health Centre
119. South Bruce Grey Health Centre - Chesley
120. South Bruce Grey Health Centre - Durham
121. South Bruce Grey Health Centre - Kincardine
122. South Bruce Grey Health Centre - Walkerton
123. South Huron Hospital
124. St. Francis Memorial Hospital
125. St. Joseph's General Hospital (Elliot Lake)
126. St. Joseph's Health Care London
127. St. Joseph's Health Care System - Hamilton
128. St. Mary's General Hospital
129. St. Thomas Elgin General Hospital
130. Stevenson Memorial Hospital - Alliston
131. Strathroy Middlesex General Hospital
132. Sunnybrook Health Sciences Centre
133. Temiskaming Hospital
134. The Lady Minto Hospital
135. The Red Lake Margaret Cochenour Memorial Hospital
136. Thunder Bay Regional Health Sciences Centre
137. Tillsonburg District Memorial Hospital
138. Timmins and District Hospital
139. Toronto East Health Network - Michael Garron Hospital
140. Toronto General Hospital
141. Trillium Health Partners - Credit Valley
142. Trillium Health Partners - Mississauga
143. Trillium Health Partners - Queensway Health
144. Unity Health Toronto - St. Joseph's
145. West Haldimand General Hospital
146. West Nipissing General Hospital
147. West Parry Sound Health Centre
148. William Osler Health System
149. Wilson Memorial General Hospital
150. Winchester District Memorial Hospital
151. Windsor Regional Hospital - Metropolitan Campus
152. Windsor Regional Hospital - Ouellette Campus
153. Wingham and District Hospital
154. Woodstock Hospital

**Instructions:**

**PRIORITY ORDER (most important first):**
1. **city** - REQUIRED. The city where the hospital is located. This is the most important field.
2. **address** - IMPORTANT. Street address (number and street name only, no city/province/postal code)
3. **latitude/longitude** - OPTIONAL. Only include if you are confident in the accuracy. Leave blank if unsure.
4. **phone** - OPTIONAL. Main hospital phone number with area code.

**Other rules:**
- Use the hospital_name exactly as listed above
- If a hospital has multiple campuses, use data for the specific campus listed
- If you cannot find a field, leave it blank (not "UNKNOWN")
- Format as CSV with the header row included
- Include ALL 154 hospitals

**Example with all fields:**
```
CHEO (Children's Hospital of Eastern Ontario),Ottawa,401 Smyth Road,45.4014,-75.6515,613-737-7600
```

**Example with only required/confident fields:**
```
Atikokan General Hospital,Atikokan,120 Dorothy Street,,,
```

**Output the complete CSV data.**
