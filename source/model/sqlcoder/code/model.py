import logging
import math
import os
from threading import Thread

import sqlparse
import torch
import transformers
from djl_python import Input, Output
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

device = "cuda"


def load_model(properties):
    model_location = properties["model_dir"]
    if "model_id" in properties:
        model_location = properties["model_id"]
    logging.info(f"Loading model in {model_location}")
    tokenizer = AutoTokenizer.from_pretrained(model_location, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_location,
        trust_remote_code=True,
        load_in_8bit=True,
        device_map="auto",
        use_cache=True,
    )
    return tokenizer, model


model = None
tokenizer = None


def generate_prompt(question):
    prompt = """### Task
Generate a SQL query to answer [QUESTION]{question}[/QUESTION]

### Instructions
- If you cannot answer the question with the available database schema, return 'I do not know'
- Remember that revenue is price multiplied by quantity
- Remember that cost is supply_price multiplied by quantity

### Database Schema
This query will run on a database whose schema is represented in this string:
CREATE TABLE products (
  product_id INTEGER PRIMARY KEY, -- Unique ID for each product
  name VARCHAR(50), -- Name of the product
  price DECIMAL(10,2), -- Price of each unit of the product
  quantity INTEGER  -- Current quantity in stock
);

CREATE TABLE customers (
   customer_id INTEGER PRIMARY KEY, -- Unique ID for each customer
   name VARCHAR(50), -- Name of the customer
   address VARCHAR(100) -- Mailing address of the customer
);

CREATE TABLE salespeople (
  salesperson_id INTEGER PRIMARY KEY, -- Unique ID for each salesperson
  name VARCHAR(50), -- Name of the salesperson
  region VARCHAR(50) -- Geographic sales region
);

CREATE TABLE sales (
  sale_id INTEGER PRIMARY KEY, -- Unique ID for each sale
  product_id INTEGER, -- ID of product sold
  customer_id INTEGER,  -- ID of customer who made purchase
  salesperson_id INTEGER, -- ID of salesperson who made the sale
  sale_date DATE, -- Date the sale occurred
  quantity INTEGER -- Quantity of product sold
);

CREATE TABLE product_suppliers (
  supplier_id INTEGER PRIMARY KEY, -- Unique ID for each supplier
  product_id INTEGER, -- Product ID supplied
  supply_price DECIMAL(10,2) -- Unit price charged by supplier
);

-- sales.product_id can be joined with products.product_id
-- sales.customer_id can be joined with customers.customer_id
-- sales.salesperson_id can be joined with salespeople.salesperson_id
-- product_suppliers.product_id can be joined with products.product_id

### Answer
Given the database schema, here is the SQL query that answers [QUESTION]{question}[/QUESTION]
[SQL]
"""
    prompt = prompt.format(question=question)
    return prompt


def stream_items(sql_query):
    chunks = sql_query.split("\n")
    for chunk in chunks:
        stream_buffer = chunk + "\n"
        logging.info(f"Stream buffer: {stream_buffer}")
        yield stream_buffer


def handle(inputs: Input):
    global tokenizer, model
    if not model:
        tokenizer, model = load_model(inputs.get_properties())

    if inputs.is_empty():
        return None
    data = inputs.get_as_json()

    prompt = data["prompt"]
    stream = data.get("stream", False)

    # updated_prompt = generate_prompt(prompt)
    updated_prompt = prompt

    inputs = tokenizer(updated_prompt, return_tensors="pt").to("cuda")
    generated_ids = model.generate(
        **inputs,
        num_return_sequences=1,
        eos_token_id=tokenizer.eos_token_id,
        pad_token_id=tokenizer.eos_token_id,
        max_new_tokens=400,
        do_sample=False,
        num_beams=1,
    )
    decoded_outputs = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)
    sql_query = sqlparse.format(decoded_outputs[0].split("[SQL]")[-1], reindent=True)
    logging.info(f"SQL Query: {sql_query}")

    outputs = Output()
    # split SQL query every into chunks containing 10 characters
    if stream:
        outputs.add_stream_content(stream_items(sql_query), output_formatter=None)
    else:
        outputs.add_as_json({"outputs": sql_query})

    return outputs
