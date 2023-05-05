---
title: Guide - Blocks And Automations
slug: prefect/blocks-automations
excerpt: Discover blocks and automations in prefect to send notifications such as Emails
section: Prefect
order: 02
updated: 2023-05-06
---

**Last updated 06th April 2023**
 
## Objective

The purpose of this tutorial is to show you how to send a notification (in this case an email) with Prefect. This result will be achieved through 2 tools: blocks and automations. At the end of the tutorial, you will be able to send an email via Prefect. You will also be able to understand the concept of blocks and automations and how to use them.  
 
## Requirements

- The tutorial [Guide - Getting started]()
- An address mail

## Instructions
 
### What is a Block ?

In Prefect, "blocks" are pre-built, reusable building blocks that encapsulate common tasks or operations. They are designed to make it easier for users to build workflows by abstracting away the underlying complexity and allowing them to focus on the high-level logic of their pipelines. Blocks can be thought of as building blocks that can be pieced together to create complex workflows. They are created and maintained by the Prefect community and can be easily shared and used by other users.

To access the lists of blocks, go on your prefect cloud account. In the sidebar, you can see the tab Blocks. Click on it and you will be able to see a list of software. It can be Docker, Github,json... Here, we will use the Email Block. It should be something similar as this : 

[!image](images/email_block.png){.thumbnail}

Click on add and fill the block with a name and the address mail where you will receive a notification. You can enter multiple address mails. Your block has been created, now let's see what is an automation and why it will be useful to send our email. 

### What is an automation ?

In Prefect, an automation is a higher-level construct that allows you to orchestrate and automate workflows using a set of pre-defined rules and conditions. It provides an easy-to-use interface for configuring, scheduling, and monitoring the execution of workflows, making it easier for developers to manage and maintain their pipelines. Automations can be used to trigger workflows based on specific events or data conditions, schedule workflows to run at specific times or intervals, and handle errors and exceptions in a more streamlined manner. 

In our case, we will use automation to send a notification. Thanks to the block **Email**, we will create a notification through an automation. This automation can only be create on the Prefect cloud's UI. Some others automations can also be create by the agent in python's code. Now let's go on the side bar of our workspace, select **Automations** and click on the + icon. 

The first step to complete is the trigger. For this example, we will send an email when the flow of the getting started is completed. You can fill the page like this :

[!image](images/trigger.png){.thumbnail}

> [!primary]
>
> You can select multiple flows if you want to send the same email if multiples flows entered the state completed. 
>

After you will have to describe the action to do when your flow (created in the getting started) will finish. Here, we want to send a notification, more precisely an email. To do it, really simple ! We choose send a notification as an action type, then we choose the email block we create before and we define the subject of the email and the body. The creation of the automation is responsive. The suggestions will vary depending on the action chosen. Your actions page should look something like this : 

[!image](images/actions.png){.thumbnail}

Last page, you have to fill the details of your automations like the name and the description. Choose a name and a description as you want. Ok now let's run your flow ! Wait until your flow is completed and... Check your mailbox, we will receive a mail from prefect ! 

## Go further

If you want to know more about [Blocks in Prefect](https://docs.prefect.io/concepts/blocks/)

If you want to know more about [Automations in Prefect](https://docs.prefect.io/ui/automations/)

Mettre ici un lien pour le tutorial end to end pipeline.  
 
Join our community of users on <https://community.ovh.com/en/>.