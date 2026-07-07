# OpenData SG Dataset

Local LakeBench OpenData_SG layout.

## Structure

```text
opendata_sg/
  downloads/
  ground_truth/
    webtable_join_ground_truth.csv
  query/
    webtable_join_query.csv
  tables/
    datasets_SG/
      SG_CSV*.csv
```

The raw `datasets_SG` CSV files were copied from:

```text
/home/hylee/aist/dynamic-join-index/OpenData_SG/datasets_SG
```

The query and ground-truth files are copied from the local WebTable Join benchmark because the LakeBench README associates `OpenData_SG` with `WebTable_Join_Query` and `WebTable_Join_Ground_Truth`.
