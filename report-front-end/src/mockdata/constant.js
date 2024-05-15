export const data_analyse = '根据给定的数据,销量前10的商品及其销量如下:' +
    '\n1. 商品ID为0790267c-c708-424d-81f5-46903a9c8444的商品,销量为65件。' +
    '\n2. 商品ID为575c0ac0-5494-4c64-a886-a9c0cf8b779a的商品,销量为48件。 ' +
    '\n3. 商品ID为b20ba076-58a7-4602-9b56-4bee46e98388的商品,销量为46件。' +
    '\n4. 商品ID为aff05423-76e8-4339-a478-fc17d51ed985的商品,销量为44件。' +
    '\n5. 商品ID为0987bfa1-0a23-4b90-8882-8a6e9bd91e24的商品,销量为42件。' +
    '\n6. 商品ID为a6f43f84-a89a-446f-8adc-8b1a23a30a81的商品,销量为21件。' +
    '\n7. 商品ID为24c62ad2-6977-4f69-be75-e37d897c1434的商品,销量为20件。' +
    '\n8. 商品ID为9c1a2048-7aac-4565-b836-d8d4f726322c的商品,销量为16件。' +
    '\n9. 商品ID为4496471c-b098-4915-9a1a-8b9e60043737的商品,销量为14件。 ' +
    '\n10. 商品ID为5afced84-ed2d-4520-a06d-dcfeab382e52的商品,销量为14件。'

export const sql = "SELECT \n `item_id`, \n COUNT(`user_id`) AS sales_count\nFROM \n `interactions`\nWHERE\n `event_type` = 'Purchase'\nGROUP BY\n `item_id`\nORDER BY \n sales_count DESC\nLIMIT 10;\n";
export const sql_gen_process = "\n这个查询首先从 `interactions` 表中选择出所有 `event_type` 为 'Purchase' 的记录，这代表用户购买了商品。然后按照 `item_id` 对购买记录进行分组计数，得到每个商品的销量。最后按销量降序排列并限制输出前 10 行记录，包含了商品 ID 和对应的销量数。";