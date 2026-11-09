```mermaid
---
config:
  flowchart:
    curve: linear
---
graph TD;
	__start__([<p>__start__</p>]):::first
	trier(trier)
	agent(agent)
	tools(tools)
	valider(valider)
	creer_ticket(creer_ticket)
	__end__([<p>__end__</p>]):::last
	__start__ --> trier;
	agent -.-> creer_ticket;
	agent -.-> tools;
	agent -.-> valider;
	tools --> agent;
	trier --> agent;
	valider -.-> __end__;
	valider -.-> creer_ticket;
	creer_ticket --> __end__;
	classDef default fill:#f2f0ff,line-height:1.2
	classDef first fill-opacity:0
	classDef last fill:#bfb6fc

```
