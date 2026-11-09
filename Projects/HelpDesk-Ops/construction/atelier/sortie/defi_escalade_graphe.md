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
	escalader(escalader)
	__end__([<p>__end__</p>]):::last
	__start__ --> trier;
	agent -.-> __end__;
	agent -.-> tools;
	tools --> agent;
	trier -.-> agent;
	trier -.-> escalader;
	escalader --> __end__;
	classDef default fill:#f2f0ff,line-height:1.2
	classDef first fill-opacity:0
	classDef last fill:#bfb6fc

```
