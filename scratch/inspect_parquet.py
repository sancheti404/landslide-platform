import pandas as pd
import numpy as np

df = pd.read_parquet('ml/data/processed/rainfall/uttarakhand_grid_rainfall_cache.parquet')
# Check nearest grid point to (30.529505, 79.085957)
df['dist'] = np.sqrt((df['latitude'] - 30.529505)**2 + (df['longitude'] - 79.085957)**2)
nearest = df[df['timestamp'] == '2023-07-15'].sort_values('dist').iloc[0]
print("Nearest grid in parquet for 2023-07-15:")
print(nearest[['grid_id', 'latitude', 'longitude', 'timestamp', 'rainfall_3d_mm', 'dynamic_rainfall_trigger_score', 'dist']])
