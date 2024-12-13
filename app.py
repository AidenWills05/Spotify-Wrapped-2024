from flask import Flask, render_template
import pandas as pd
import plotly.express as px
import os

app = Flask(__name__)
CSV_FOLDER = os.path.abspath('csv_files')

def load_csv_data():
    try:
        files = {
            "total_minutes_2024": "total_minutes_2024.csv",
            "total_minutes_2023": "total_minutes_2023.csv",
            "top_100_songs_2024": "top_100_songs_2024.csv",
            "top_100_songs_2023": "top_100_songs_2023.csv",
            "monthly_minutes_2024": "monthly_minutes_2024.csv",
            "monthly_minutes_2023": "monthly_minutes_2023.csv",
            "top_50_artists_2024": "top_50_artists_2024.csv",
            "top_50_artists_2023": "top_50_artists_2023.csv",
            "top_10_artists_2024": "top_10_artists_2024.csv",
        }

        data = {}
        for key, file in files.items():
            file_path = os.path.join(CSV_FOLDER, file)
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Missing required file: {file}")
            df = pd.read_csv(file_path)
            if df.empty:
                raise ValueError(f"File {file} is empty.")
            data[key] = df

        return data
    except Exception as e:
        print(f"Error loading data: {e}")
        return None

def compute_percentage(df, total_minutes):
    """Compute percentage of total minutes for each entry."""
    df['Percentage'] = (df['Minutes Played'] / total_minutes) * 100
    return df

@app.route('/')
def index():
    data = load_csv_data()
    if data is None:
        return "Error: Unable to load data. Check the terminal for details."

    # Total Minutes Comparison
    total_minutes_2024 = data['total_minutes_2024'].iloc[0]['Total Minutes']
    total_minutes_2023 = data['total_minutes_2023'].iloc[0]['Total Minutes']
    diff = total_minutes_2024 - total_minutes_2023
    percentage_change = (diff / total_minutes_2023) * 100

    total_minutes_comparison = {
        '2024 Total Minutes': total_minutes_2024,
        'Difference': diff,
        'Percentage Change': round(percentage_change, 2),
    }

    # Monthly Listening Times Data
    monthly_diff = []
    for m_2024, m_2023 in zip(data['monthly_minutes_2024'].to_dict('records'),
                              data['monthly_minutes_2023'].to_dict('records')):
        diff = m_2024['Minutes Played'] - m_2023['Minutes Played']
        percentage = (diff / m_2023['Minutes Played']) * 100 if m_2023['Minutes Played'] != 0 else 0
        monthly_diff.append({
            'Month': m_2024.get('Month', 'Unknown'),
            'Minutes Played': m_2024.get('Minutes Played', 0),
            'Difference': diff,
            'Percentage Change': round(percentage, 2),
        })

    # Top 10 Artists Per Month Graph
    top_10_artists_df = data['top_10_artists_2024']
    
    # Add Month Numbers for Sorting
    month_map = {
        'January': 1, 'February': 2, 'March': 3, 'April': 4,
        'May': 5, 'June': 6, 'July': 7, 'August': 8,
        'September': 9, 'October': 10, 'November': 11, 'December': 12
    }
    top_10_artists_df['MonthNumber'] = top_10_artists_df['Month'].map(month_map)
    
    # Aggregate Total Listening Time per Artist
    artist_totals = top_10_artists_df.groupby('Artist', as_index=False)['Minutes Played'].sum()
    artist_totals = artist_totals.sort_values('Minutes Played', ascending=False)

    # Merge Totals Back to Main Data for Sorting
    top_10_artists_sorted = pd.merge(top_10_artists_df, artist_totals, on='Artist', suffixes=('', '_Total'))
    
    # Final Sorted Data
    category_order = artist_totals['Artist'].tolist()
    top_artists_per_month_graph = px.bar(
        top_10_artists_sorted,
        x='Artist',
        y='Minutes Played',
        color='MonthNumber',
        title="Top Artists Per Month in 2024 (Sorted by Total Listening Time)",
        category_orders={'Artist': category_order},
        color_continuous_scale=px.colors.sequential.Plasma,
        height=600,
    ).update_traces(
        hovertemplate="Artist: %{x}<br>Month: %{customdata}<br>Minutes Played: %{y}<extra></extra>",
        customdata=top_10_artists_sorted['Month']
    )

    # Compute Percentages for Top Songs and Artists
    songs_2024 = compute_percentage(data['top_100_songs_2024'].head(30), total_minutes_2024)
    songs_2023 = compute_percentage(data['top_100_songs_2023'].head(30), total_minutes_2023)
    artists_2024 = compute_percentage(data['top_50_artists_2024'].head(25), total_minutes_2024)
    artists_2023 = compute_percentage(data['top_50_artists_2023'].head(25), total_minutes_2023)

    # Calculate height dynamically (e.g., 50 pixels per row)
    height_2024_songs = len(data['top_100_songs_2024'].head(30)) * 50
    height_2023_songs = len(data['top_100_songs_2023'].head(30)) * 50

    # Top 30 Songs Graphs
    top_30_songs_graph_2024 = px.bar(
        songs_2024,
        y='Song Name',
        x='Minutes Played',
        title="Top 30 Songs in 2024",
        orientation='h'
    ).update_traces(
        hovertemplate="Minutes Played: %{x}<br>Song Name: %{y}<br>Percentage of Year: %{customdata:.2f}%<extra></extra>",
        customdata=songs_2024['Percentage']
    ).update_layout(
	plot_bgcolor="#e2dcdc",  # Light off-white for graph background
    	paper_bgcolor="#e2dcdc",  # Light off-white for outer background
   	 font_color="black",  # Adjusted font color for contrast
        hoverlabel=dict(
        bgcolor="cornflowerblue",
        font_color="white"
 ),
    yaxis=dict(
        tickmode="linear",
        dtick=1,
        automargin=True
    ),
    xaxis=dict(
        range=[0, 450],  # Set x-axis range from 0 to 5000
        title="Minutes Played"
    ),
    height=575
)
    top_30_songs_graph_2023 = px.bar(
        songs_2023,
        y='Song Name',
        x='Minutes Played',
        title="Top 30 Songs in 2023",
        orientation='h'
    ).update_traces(
        hovertemplate="Minutes Played: %{x}<br>Song Name: %{y}<br>Percentage of Year: %{customdata:.2f}%<extra></extra>",
        customdata=songs_2023['Percentage']
    ).update_layout(
	plot_bgcolor="#e2dcdc",  # Light off-white for graph background
   	paper_bgcolor="#e2dcdc",  # Light off-white for outer background
   	font_color="black",  # Adjusted font color for contrast
        hoverlabel=dict(
        bgcolor="cornflowerblue",
        font_color="white"
 ),
    yaxis=dict(
        tickmode="linear",
        dtick=1,
        automargin=True
    ),
    xaxis=dict(
        range=[0, 450],  # Set x-axis range from 0 to 5000
        title="Minutes Played"
    ),
    height=575
)

    # Top 25 Artists Graphs
    top_25_artists_graph_2024 = px.bar(
        artists_2024,
        y='Artist',
        x='Minutes Played',
        title="Top 20 Artists in 2024",
        orientation='h'
    ).update_traces(
        hovertemplate="Minutes Played: %{x}<br>Artist: %{y}<br>Percentage of Year: %{customdata:.2f}%<extra></extra>",
        customdata=artists_2024['Percentage']
    ).update_layout(
	plot_bgcolor="#e2dcdc",  # Light off-white for graph background
    	paper_bgcolor="#e2dcdc",  # Light off-white for outer background
    	font_color="black",  # Adjusted font color for contrast
    	hoverlabel=dict(
        bgcolor="#000000",
        font=dict(color="white"),
    ),
    yaxis=dict(
        tickmode="linear",
        dtick=1,
        automargin=True
    ),
    xaxis=dict(
        range=[0, 7500],  # Set x-axis range from 0 to 5000
        title="Minutes Played"
    ),
    height=600
)

    top_25_artists_graph_2023 = px.bar(
        artists_2023,
        y='Artist',
        x='Minutes Played',
        title="Top 20 Artists in 2023",
        orientation='h'
    ).update_traces(
        hovertemplate="Minutes Played: %{x}<br>Artist: %{y}<br>Percentage of Year: %{customdata:.2f}%<extra></extra>",
        customdata=artists_2023['Percentage']
    ).update_layout(
	plot_bgcolor="#e2dcdc",  # Light off-white for graph background
    	paper_bgcolor="#e2dcdc",  # Light off-white for outer background
    	font_color="black",  # Adjusted font color for contrast
    	hoverlabel=dict(
        bgcolor="#000000",
        font=dict(color="white"),
    ),
    yaxis=dict(
        tickmode="linear",
        dtick=1,
        automargin=True
    ),
    xaxis=dict(
        range=[0, 7500],  # Set x-axis range from 0 to 5000
        title="Minutes Played"
    ),
    height=600
)

    return render_template(
        'index.html',
        total_minutes_comparison=total_minutes_comparison,
        monthly_minutes_2024=monthly_diff,
        top_30_songs_graph_2024=top_30_songs_graph_2024.to_html(full_html=False),
        top_30_songs_graph_2023=top_30_songs_graph_2023.to_html(full_html=False),
        top_25_artists_graph_2024=top_25_artists_graph_2024.to_html(full_html=False),
        top_25_artists_graph_2023=top_25_artists_graph_2023.to_html(full_html=False),
        top_artists_per_month_graph=top_artists_per_month_graph.to_html(full_html=False),
    )

if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=8080)
