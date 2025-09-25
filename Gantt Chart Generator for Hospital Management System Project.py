import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
from datetime import datetime
import numpy as np

# Define the project tasks and their dates
tasks = [
    {'Task': 'Requirements Analysis', 'Start': '2025-07-01', 'End': '2025-07-15'},
    {'Task': 'Literature Review', 'Start': '2025-07-08', 'End': '2025-07-22'},
    {'Task': 'System Design', 'Start': '2025-07-15', 'End': '2025-07-29'},
    {'Task': 'Database Design', 'Start': '2025-07-22', 'End': '2025-08-05'},
    {'Task': 'Backend Development (Flask)', 'Start': '2025-07-29', 'End': '2025-08-19'},
    {'Task': 'Frontend Development (Bootstrap)', 'Start': '2025-08-05', 'End': '2025-08-26'},
    {'Task': 'Core Features Implementation', 'Start': '2025-08-12', 'End': '2025-09-09'},
    {'Task': 'Testing & Debugging', 'Start': '2025-09-02', 'End': '2025-09-16'},
    {'Task': 'Documentation', 'Start': '2025-09-09', 'End': '2025-09-23'},
    {'Task': 'Final Report Preparation', 'Start': '2025-09-16', 'End': '2025-09-25'}
]

# Convert to DataFrame
df = pd.DataFrame(tasks)
df['Start'] = pd.to_datetime(df['Start'])
df['End'] = pd.to_datetime(df['End'])
df['Duration'] = (df['End'] - df['Start']).dt.days

# Create the figure and axis
fig, ax = plt.subplots(figsize=(12, 8))

# Create colors for each task
colors = plt.cm.Set3(np.linspace(0, 1, len(df)))

# Plot each task
for i, task in enumerate(df.itertuples()):
    ax.barh(task.Task, task.Duration, left=task.Start, 
            color=colors[i], edgecolor='black', alpha=0.8)

# Format the date axis
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
fig.autofmt_xdate()

# Add labels and title
ax.set_xlabel('Timeline')
ax.set_ylabel('Tasks')
ax.set_title('Hospital Management System Project Gantt Chart')

# Add grid
ax.grid(axis='x', linestyle='--', alpha=0.7)

# Add legend
ax.legend(df['Task'], bbox_to_anchor=(1.05, 1), loc='upper left')

# Adjust layout
plt.tight_layout()

# Show the plot
plt.show()

# Save the plot
plt.savefig('hospital_management_gantt_chart.png', dpi=300, bbox_inches='tight')