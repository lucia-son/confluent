import findspark
import pyspark
from pyspark.sql import SparkSession
from pyspark.sql.functions import regex_replace

archive_destination_path="/engn"
config_base_path=archive_destination_path | regex_replace('\\/$','')

print("config_base_path: " + config_base_path)
 
