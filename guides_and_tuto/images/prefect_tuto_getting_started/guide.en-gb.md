---
title: Guide - Getting Started
slug: prefect/getting-started
excerpt: Discover Prefect and configure it for your first workflows
section: Prefect
order: 01
updated: 2024-04-06
---


**Last updated 06th April, 2023**
 
## Objective
 
The purpose of this guide is to discover [Prefect](https://docs.prefect.io/), an open source workflow management tool, and connect it to the [OVHcloud API](https://api.ovh.com/). Prefect provides a flexible Python framework to easily combine tasks into workflows, then deploy, schedule, and monitor their execution through the Prefect UI or API. 
 
## Requirements

- Access to the [OVHcloud Control Panel](https://www.ovh.com/auth/?action=gotomanager&from=https://www.ovh.co.uk/&ovhSubsidiary=GB)
- Access to the [OVHcloud API](https://api.ovh.com/). We can found more information [here](https://docs.ovh.com/gb/en/api/first-steps-with-ovh-api/). Be sure your application token can access the GET request **/cloud** and the GET request **/me**. 
- A [Public Cloud project](https://www.ovhcloud.com/en-gb/public-cloud/)

## Instructions

### What is Prefect ? 

Prefect is an open source tool used to build, schedule and monitor workflows. You can compare it to Apache Airflow for the global approach. A workflow management tool is useful to create and automate your pipelines, most often data pipelines or AI pipelines but not only. 

Prefect works with local agent on your execution environment (your own computer, a virtual machine, ...) and a server who will interact with your agent. This server can be installed by yourself (**Self-hosted**) or launched via their Prefect cloud offer..

It can be seen as follow:

[!image](images/agent_server.png){.thumbnail} 

