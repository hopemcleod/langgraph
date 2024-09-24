The objective of this project is learn how to create agentic workflows and work with LLMs. It also has scope to introduce Retrieval Augmented Generation (RAG) into the process.
**This project is not trying to build something for production. It is meant as a learning exercise.**

The workflow starts of with the user (therapist?) asking for a report to be generated on the best exercises for a musculo-skeletal (MSK) diagnosis using evidence based literature as the source. In addition, the workflow could create a letter that takes the report findings and a musculo-
The general workflow is:
```user query``` -> ```plan web search based on query``` -> ```select best n results``` -> ```scrap data from resulting web pages``` -> ```generate report from scrapings```

Additionally could go on to:

```report``` -> ```letter``` <- ```MSK complaint```