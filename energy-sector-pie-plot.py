import matplotlib.pyplot as plt


plt.rcParams['font.size'] = 20
plt.rcParams['font.weight'] = 'bold'

labels = 'Motors', 'Heater', 'Fans', 'Others'
sizes = [51.7, 40.4, 6.9, 1.0]
colors = ['#C44440', '#6666FF', '#A0C289', 'gold']

explode = [0.01, 0.01, 0.3, 0.03]


patches, texts, autotexts = plt.pie(sizes, explode=explode, labels=None, colors=colors, startangle=90, autopct='%1.1f%%')

patches[0].set_hatch('/')
patches[1].set_hatch('\\')
patches[2].set_hatch('|')
#patches[3].set_hatch('|')



plt.axis('equal')
plt.legend(patches, labels, loc="east")

texts[2] = ''

plt.show()