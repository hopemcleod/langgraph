**This project is not trying to build something for production. It is meant as a learning exercise.**

The objective of this project is learn how to create agentic workflows and work with LLMs. It also has scope to introduce Retrieval Augmented Generation (RAG) into the process.


The workflow starts off with the user (therapist?) asking for a report to be generated on the best exercises for a musculo-skeletal (MSK) complaint, using evidence based literature as the source. In addition, the workflow could create a letter that specifies the exercises that will most likely be used as part of a treatment programme.

The general workflow is:<br><br>
```user query``` -> ```plan web search based on query``` -> ```select best n results``` -> ```scrap data from resulting web pages``` -> ```generate report from scrapings```<br>

Additionally could go on to:<br>

```report``` -> ```letter``` <- ```MSK complaint```