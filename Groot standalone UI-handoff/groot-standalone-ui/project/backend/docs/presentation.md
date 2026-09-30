# GROOT presentation guide

## The idea in one sentence

People should be able to say what they need to know in everyday language; GROOT turns that request into information to check, keeps the sources with the answer, and remembers what happened after a choice.

## What to say while opening the website

“This is GROOT. It helps a team move from a question to the information needed to make a choice. The website shows the product idea. I’ll also show sample tasks running in the local service.”

The website and the service are two separate demonstrations. The website's built-in buttons still use sample behavior from the original design. The local service is the part that saves new tasks and results.

## A four-minute service walkthrough

### 1. Start with a direct answer

Ask: **“What were Q2 sales in Maharashtra?”**

Say: “GROOT found two matching rows in the sample sales records, added them to ₹278 lakh, and showed the source. These are made-up company numbers.”

### 2. Show a choice that needs more information

Ask: **“Should we move 30% of production from Supplier A to B for Q4?”**

Say: “Supplier B's sample price is lower, but price alone is not enough. GROOT marks Q4 capacity as a key fact to check before anyone saves a choice. It also lists delivery time, defect rate, minimum order and setup cost.”

Show the facts being checked one at a time. Each reply says which sample record the information came from. The example estimates that Supplier B could be 2,100 units short if it takes on 30% of Supplier A's current Q4 amount. Explain that this estimate uses made-up numbers and is a warning for a person to review, not a final answer. Once all six facts are checked, save the human choice.

### 3. Show how a later result changes a future task

Record: **“Supplier B met Q4 volume; lead time ran four days longer than planned.”**

Say: “GROOT saved what the team chose and what later happened. When I ask the supplier question again, capacity appears as an important check because it mattered in the previous choice.”

### 4. Show meeting input with consent

Start a Decision Room session and enter this written statement: **“We don't have a recent capacity confirmation.”**

Say: “The service asks for consent before it accepts meeting statements. This demo uses text that I type; it does not listen to a microphone. GROOT marks capacity as missing, but the statement itself is not proof.”

Or use the four prepared meeting statements from the demo request file. Close the session after showing the updated supplier task.

### 5. If there is time

- Ask why sales fell in the North in Q2 2026. The sample records show a 14.1% decrease. GROOT shows changes by sales channel, but it does not pretend the records prove the cause.
- Search for eight manufacturers with ISO 9001 and monthly capacity above 15,000 units. The reply returns up to eight matching made-up records.

## If someone asks what is real

- The task steps, saving, sample record checks, consent requirement, and history loop run in the local service.
- The supplier, sales and manufacturer records are fictional.
- The meeting example is typed text, not live listening.
- The demo uses fixed rules rather than an AI model. This makes the presentation repeatable and shows the product flow; it is not the finished product.
- No real company records are read, no outside research is run, and GROOT does not make the choice for a person.

For exact requests, see [`../demo.http`](../demo.http). For setup help, see [`../README.md`](../README.md).
