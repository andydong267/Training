import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.dynamicframe import DynamicFrame
from pyspark.sql.functions import regexp_replace,col

## @params: [JOB_NAME]
args = getResolvedOptions(sys.argv, ['JOB_NAME'])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

## Read from AWS Catalog
df = glueContext.create_dynamic_frame.from_catalog(database = "gluebucket267", table_name="covid_19_data_csv")
data=df.toDF()

## Perform Transformation
data = data.withColumn('Country/Region', regexp_replace(col('Country/Region'), ",", ""))
data = data.withColumn('Country/Region', regexp_replace(col('Country/Region'), "'", ""))
data = data.withColumn('Country/Region', regexp_replace(col('Country/Region'), r"\(", ""))
data = data.withColumn('Country/Region', regexp_replace(col('Country/Region'), r"\)", ""))

data = data.groupBy('Country/Region', 'Province/State').max().orderBy('Country/Region')
data = data.drop('max(SNo)')

## Output
dynamic = DynamicFrame.fromDF(data, glueContext, "dyf")
dynamic_less = dynamic.coalesce(1)
#datasink = glueContext.write_dynamic_frame.from_catalog(frame = dynamic, database = "gluebucket267", table_name="covid_19_data_csv", transformation_ctx="datasink")

glueContext.write_dynamic_frame.from_options(
    frame = dynamic_less,
    connection_type="s3",
    format="parquet",
    connection_options={
        "path": "s3://hexabucket267/new",
    }
    )

job.commit()