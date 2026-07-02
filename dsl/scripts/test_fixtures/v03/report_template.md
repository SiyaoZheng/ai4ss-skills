# {{ paper.title }}

Schema: {{ schema }}

Objects:
{% for item in objects %}{% if item.category %}- {{ item.id }} [{{ item.kind }}]
{% endif %}{% endfor %}

Couplings:
{% for rel in relations %}{% if rel.asserted_by %}- {{ rel.id }}: {{ rel.type }}
{% endif %}{% endfor %}
