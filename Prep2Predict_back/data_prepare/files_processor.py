import pandas as pd
from pandas.api.types import is_string_dtype, is_numeric_dtype
from pathlib import Path
from fastapi import UploadFile, File
from data_prepare import convert_int as ci
import db_connection as db
from models.files_db_model import *

async def save_file(file: UploadFile = File(...)):
    try:
        with db.conn.atomic():
            db.conn.execute_sql("TRUNCATE TABLE Prep2Predict.properties, Prep2Predict.files;")
            Path("csv_data_analysis").mkdir(parents=True, exist_ok=True)
            path = Path("csv_data_analysis", str(file.filename))
            with open(path, "wb") as f:
                f.write(await file.read())

            df = pd.read_csv(path)
            columns = df.columns.tolist()
            nulls_columns = []
            for column in columns:
                if df[column].isnull().any():
                    nulls_columns.append(column)

            new_file = FilesDBModel()
            new_file.path = str(path)
            new_file.save()

            return {
                "path": str(path),
                "columns": columns,
                "nulls_columns": nulls_columns,
                "records": df.shape[0],
            }

    except Exception as e:
        print(e)


def clean_nulls_columns(csv_path: str, nulls: dict):

    df = pd.read_csv(csv_path)

    response = {}
    for c in nulls.keys():
        if nulls[c] == 'drop':
            df = df.dropna(subset=[c])
            response[c] = "Registros nulos borrados"

        elif type(nulls[c]) == dict:
            if is_string_dtype(df[c]):
                df[c] = df[c].fillna(nulls[c]["default_value"])
                response[c] = f"Registros nulos reasignados a: {nulls[c]["default_value"]}"
            elif is_numeric_dtype(df[c]):
                df[c] = df[c].fillna(nulls[c]["default_value"])
                response[c] = f"Registros nulos reasignados a: {nulls[c]["default_value"]}"

    df.to_csv(csv_path, index=False, encoding="utf-8")
    groups_columns = ci.convert_columns_to_int(csv_path, list(df.columns))

    return {"response": response, "groups_columns": groups_columns}
