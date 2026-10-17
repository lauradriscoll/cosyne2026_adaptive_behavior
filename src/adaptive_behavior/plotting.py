"""
src/adaptive_behavior/plotting.py
Plotting helpers used by the figure notebooks.

Ported verbatim (except where noted) from aind-vr-foraging-paper
(aind_vr_foraging_analysis.utils.plotting.general_plotting_utils):
trial_collection, raster_with_velocity, plot_condition_comparison.
"""

import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.legend_handler import HandlerBase
from matplotlib.lines import Line2D
from matplotlib.image import BboxImage
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
from matplotlib.transforms import Bbox, TransformedBbox
from scipy.stats import ttest_ind, ttest_rel


class ImageHandler(HandlerBase):
    """Legend handler that draws an image (array) as the legend marker.

    Usage: ax.legend(handles, labels, handler_map={handle: ImageHandler(img)})
    """

    def __init__(self, img, **kwargs):
        super().__init__(**kwargs)
        self.img = img

    def create_artists(self, legend, orig_handle, xdescent, ydescent, width, height,
                       fontsize, trans):
        side = min(width, height)  # keep the icon square
        x0 = xdescent + (width - side) / 2
        y0 = ydescent + (height - side) / 2
        bbox = TransformedBbox(Bbox.from_bounds(x0, y0, side, side), trans)
        return [BboxImage(bbox, data=self.img, interpolation="antialiased", zorder=5)]


def _as_image(img):
    """Accept a path or an array and return an RGBA float/uint8 array (or None)."""
    if img is None:
        return None
    return mpimg.imread(str(img)) if isinstance(img, (str, bytes)) or hasattr(img, "__fspath__") else img


def trial_collection(
    reward_sites: pd.DataFrame,
    continuous_data: pd.DataFrame,
    aligned: str = 'index',
    cropped_to_length: str = 'window',
    window: list = [-0.5, 2],
    taken_col: str = "velocity",
    resample: bool = True,
) -> pd.DataFrame:
    """
    Crop snippets of speed traces aligned to different epochs.

    Parameters
    ----------
    reward_sites : pd.DataFrame
        DataFrame containing reward site information (odor sites).
    continuous_data : pd.DataFrame
        DataFrame containing continuous data (encoder, sniffing, etc.).
    aligned : str
        Column name to align snippets to, or 'index' to use the row index.
    cropped_to_length : str
        Strategy for determining the crop window:
        'window'  — use the fixed ``window`` argument as-is (default).
        'sniff'   — crop from 0 to the next index offset.
        'patch'   — crop from time_since_entry to exit_epoch.
        'epoch'   — crop relative to epoch start/duration.
    window : list[float, float]
        [start, stop] offsets in seconds used when cropped_to_length='window'.
    taken_col : str
        Column in ``continuous_data`` to extract. Default: 'velocity'.
    resample : bool
        If True (default), interpolate each trial onto a uniform time grid so
        that every trial has identical ``times`` values spanning [w0, w1] at
        the median sample interval. NaN is used where the source data doesn't
        cover the requested window. If False, keep the original timestamps
        shifted so the alignment point is t=0.

    Returns
    -------
    pd.DataFrame
        Concatenated snippets with columns: times, time_reference, <taken_col>,
        plus all columns from ``reward_sites``.
    """
    from scipy.interpolate import interp1d

    _EMPTY = pd.DataFrame(
        columns=['times', 'time_reference', taken_col] + list(reward_sites.columns)
    )

    # Exclude the last row (mirrors original `iloc[:-1]`)
    sites = reward_sites.copy()
    if sites.empty:
        print('No trials collected, check the parameters of the function')
        return _EMPTY
    
    # Median sample interval
    samples_per_second = round(float(pd.Series(continuous_data['times']).diff().dropna().median()), 3)

    cont_index = continuous_data['times'].to_numpy()
    cont_values = continuous_data[taken_col].to_numpy()
    output_col = "velocity" if taken_col == "velocity" else taken_col

    # Pre-extract reward_sites columns once to avoid repeated attribute access
    site_records = sites.to_dict(orient='list')  # {col: [values...]}
    site_cols = list(site_records.keys())

    trial_list = []
    
    for i, (start_reward, row) in enumerate(sites.iterrows()):
        # --- Determine window bounds for this trial ---
        if cropped_to_length == 'sniff':
            w0, w1 = 0.0, float(row['next_index'] - start_reward)
        elif cropped_to_length == 'patch':
            w0, w1 = float(row['time_since_entry']), float(row['exit_epoch'])
        elif cropped_to_length == 'epoch':
            w0 = float(row['start_time'] - row[aligned])
            w1 = float(row['duration_epoch'])
        else:
            w0, w1 = float(window[0]), float(window[1])

        # --- Slice continuous data ---
        if aligned != 'index':
            ref = float(row[aligned])
            mask = (cont_index >= ref + w0) & (cont_index < ref + w1)
            raw_values = cont_values[mask]
            n = len(raw_values)
        else:
            ref = float(start_reward)
            # searchsorted is O(log n) vs boolean mask O(n) for large arrays
            lo = np.searchsorted(cont_index, ref + w0, side='left')
            hi = np.searchsorted(cont_index, ref + w1, side='right')
            raw_values = cont_values[lo:hi]
            n = hi - lo

        if n == 0:
            continue

        # Original timestamps relative to alignment point
        if aligned != 'index':
            original_times = cont_index[mask] - ref
        else:
            original_times = cont_index[lo:hi] - ref

        # --- Build uniform time grid via interpolation, or keep original ---
        if resample:
            uniform_times = np.arange(w0, w1, samples_per_second)
            f = interp1d(
                original_times,
                raw_values,
                kind='linear',
                bounds_error=False,
                fill_value=np.nan,
            )
            times = uniform_times
            trial_values = f(uniform_times)
        else:
            times = original_times
            trial_values = raw_values

        min_len = len(times)
        if min_len == 0:
            continue

        # --- Assemble trial DataFrame in one shot ---
        trial_dict: dict = {
            'times': times,
            'time_reference': ref,
            output_col: trial_values,
        }

        # Broadcast scalar site metadata without np.repeat where possible
        for col in site_cols:
            trial_dict[col] = np.broadcast_to(
                np.array([site_records[col][i]]), (min_len,)
            ).copy()  # .copy() makes it writeable if downstream code needs that

        trial_list.append(pd.DataFrame(trial_dict))

    if not trial_list:
        print('No trials collected, check the parameters of the function')
        return _EMPTY

    return pd.concat(trial_list, ignore_index=True)


def raster_with_velocity(
    active_site: pd.DataFrame,
    stream_data: pd.DataFrame,
    save=False,
    color_dict_label: dict = {
        "Ethyl Butyrate": "#d95f02",
        "Alpha-pinene": "#1b9e77",
        "Amyl Acetate": "#7570b3",
    },
    with_velocity: bool = True,
    barplots: bool = True,
    figsize: tuple = None,
    order_by: str = "patch_index",
    sniff_data: pd.DataFrame = None,
    sniff_col: str = "sniff",
    sniff_color: str = "#0d7377",
    sniff_scale: float = 0.3,
    bar_alpha: float = 0.8,
    tone_image=None,
    reward_image=None,
    marker_size_pt: float = 4.5,
):
    """tone_image / reward_image: optional path or array drawn instead of the red
    square (choice tone) / blue circle (reward) markers, `marker_size_pt` points wide.
    The legend keeps empty 'Tone' / 'Reward' handles so callers can attach an
    ImageHandler to them."""

    tone_img = _as_image(tone_image)
    reward_img = _as_image(reward_image)

    def _image_marker(img, x, y):
        box = OffsetImage(img, zoom=marker_size_pt / img.shape[1])
        ax1.add_artist(AnnotationBbox(box, (x, y), frameon=False, pad=0,
                                      zorder=5, annotation_clip=False))

    active_site = active_site.copy()

    # Build ip_durations before test_df so we can extend exit_epoch
    ip_durations = (
        active_site[active_site['site_label'] == 'InterPatch']
        .groupby('patch_index')['duration_epoch'].first()
    )

    test_df = active_site.groupby('patch_index').agg(
        {'time_since_entry': 'min', 'patch_onset': 'mean', 'exit_epoch': 'max'}
    )
    test_df.reset_index(inplace=True)
    test_df.fillna(15, inplace=True)

    # Extend exit_epoch to include the trailing interpatch of the next patch
    test_df['exit_epoch'] = test_df.apply(
        lambda r: r['exit_epoch'] + ip_durations.get(r['patch_index'] + 1, 0),
        axis=1
    )

    if len(test_df) <= 1:
        print('Not enough patches to plot raster with velocity')
        return

    trial_summary = trial_collection(
        test_df, stream_data, aligned='patch_onset', cropped_to_length='patch', taken_col='velocity'
    )

    if len(trial_summary) == 0 or trial_summary['velocity'].dropna().empty:
        print('No velocity data available for this session')
        return

    sniff_summary = None
    if sniff_data is not None and sniff_col in sniff_data.columns:
        sniff_summary = trial_collection(
            test_df, sniff_data, aligned='patch_onset', cropped_to_length='patch',
            taken_col=sniff_col,
        )
        if len(sniff_summary) == 0 or sniff_summary[sniff_col].dropna().empty:
            sniff_summary = None

    n_patches = active_site.patch_index.nunique()

    # --- Row mapping ---
    reward_rows = active_site[active_site['site_label'] == 'RewardSite']
    label_from_reward = reward_rows.groupby('patch_index')['patch_label'].agg(
        lambda s: s.mode().iat[0]
    )
    label_fallback = active_site.groupby('patch_index')['patch_label'].agg(
        lambda s: s.mode().iat[0]
    )
    patch_labels = label_from_reward.reindex(label_fallback.index).fillna(label_fallback)
    patch_order = patch_labels.rename('patch_label').reset_index()

    if order_by == 'patch_label':
        patch_order = patch_order.sort_values(['patch_label', 'patch_index'])
    row_map = {pi: pos for pos, pi in enumerate(patch_order['patch_index'])}

    fig, ax1 = figsize

    velocity_clean = trial_summary['velocity'].dropna()
    max_speed = np.quantile(velocity_clean, 0.99)
    min_speed = np.quantile(velocity_clean, 0.01)  # can be negative

    sniff_amplitude_scale = 1.0
    sniff_global_mean = 0.0
    if sniff_summary is not None:
        sniff_clean = sniff_summary[sniff_col].dropna()
        sniff_global_mean = sniff_clean.mean()
        max_sniff = np.quantile((sniff_clean - sniff_global_mean).abs(), 0.99)
        if max_sniff > 0:
            sniff_amplitude_scale = sniff_scale / max_sniff

    # patch_ends: rightmost bar end per patch in relative time
    active_site['bar_end'] = active_site['time_since_entry'] + active_site['duration_epoch']
    patch_ends = (
        active_site[active_site['site_label'] != 'InterPatch']
        .groupby('patch_index')['bar_end'].max()
    )

    drawn_velocity_patches = set()
    drawn_trail_patches = set()

    for index, row in active_site.iterrows():

        y = row_map[row['patch_index']]

        if row['site_label'] in ('InterPatch', 'InterPatch2', 'PostPatch'):
            color = "#3F3E3E"
        elif row['site_label'] == 'InterSite':
            color = '#b3b3b3'
        elif row['site_label'] == 'RewardSite':
            color = color_dict_label[row.patch_label]
            if tone_img is not None or reward_img is not None:
                # image markers (empty scatters below keep the legend handles)
                if row["has_choice"] == True:
                    if tone_img is not None:
                        _image_marker(tone_img, row.choice_cue_time - row.patch_onset, y)
                    else:
                        ax1.scatter(row.choice_cue_time - row.patch_onset, y,
                                    color='red', marker='s', s=n_patches * 0.08, zorder=5,
                                    edgecolor='black', linewidth=0.25, alpha=0.9, label='Tone')
                if row["has_reward"] == 1 and row["has_choice"] == True:
                    x_rew = row.time_since_entry + row.duration_epoch / 2
                    if reward_img is not None:
                        _image_marker(reward_img, x_rew, y)
                    else:
                        ax1.scatter(x_rew, y,
                                    color='steelblue', marker='o', s=n_patches * 0.08, zorder=5,
                                    edgecolor='black', linewidth=0.25, alpha=0.9, label='Reward')
            else:
                if row["has_choice"] == True:
                    ax1.scatter(row.choice_cue_time - row.patch_onset, y,
                                color='red', marker='s', s=n_patches * 0.08, zorder=5,
                                edgecolor='black', linewidth=0.25, alpha=0.9, label='Tone')
                if row["has_reward"] == 1 and row["has_choice"] == True:
                    ax1.scatter(row.choice_cue_time - row.patch_onset, y,
                                color='red', marker='s', s=n_patches * 0.08, zorder=5,
                                edgecolor='black', linewidth=0.25, alpha=0.9, label='Tone')
                    ax1.scatter(row.time_since_entry + row.duration_epoch / 2, y,
                                color='steelblue', marker='o', s=n_patches * 0.08, zorder=5,
                                edgecolor='black', linewidth=0.25, alpha=0.9, label='Reward')

        if barplots:
            ax1.barh(y, left=row.time_since_entry, height=0.85,
                     width=row.duration_epoch, color=color, linewidth=0.5, alpha=bar_alpha)

        # Draw trailing InterPatch of the next patch on the current row (once per patch)
        if barplots and row['patch_index'] not in drawn_trail_patches:
            next_patch = row['patch_index'] + 1
            if next_patch in ip_durations.index and row['patch_index'] in patch_ends.index:
                trail_start = patch_ends[row['patch_index']]
                trail_dur = ip_durations[next_patch]
                ax1.barh(y, left=trail_start, height=0.85,
                         width=trail_dur, color="#3F3E3E", linewidth=0.5, alpha=bar_alpha)
                drawn_trail_patches.add(row['patch_index'])

        # Draw velocity once per patch
        if with_velocity and row['patch_index'] not in drawn_velocity_patches:
            drawn_velocity_patches.add(row['patch_index'])
            current_trial = trial_summary[
                trial_summary['patch_index'] == row['patch_index']
            ]
            if not current_trial.empty:
                vel = current_trial["velocity"].clip(lower=min_speed, upper=max_speed)
                vel_ax1 = y + 0.5 - (vel - min_speed) / (max_speed - min_speed)
                ax1.plot(current_trial['times'], vel_ax1,
                         color='black', alpha=0.8, zorder=3)
                if sniff_summary is not None:
                    current_sniff = sniff_summary[
                        sniff_summary['patch_index'] == row['patch_index']
                    ]
                    if not current_sniff.empty:
                        sniff_vals = current_sniff[sniff_col] - sniff_global_mean
                        sniff_ax1 = y - sniff_vals * sniff_amplitude_scale
                        ax1.plot(current_sniff['times'], sniff_ax1,
                                 color=sniff_color, alpha=0.7, zorder=3)

    ax1.set_xlabel("Time (s)")
    sns.despine()
    ax1.set_ylim(-1, n_patches)
    ax1.invert_yaxis()

    if order_by == 'patch_label':
        ax1.set_ylabel("Patch number (grouped by type)")
        ax1.set_yticks(range(n_patches))
        ax1.set_yticklabels(patch_order['patch_index'].values + 1)
        for tick, lab in zip(ax1.get_yticklabels(), patch_order['patch_label']):
            tick.set_color(color_dict_label.get(lab, 'black'))
        labels_arr = patch_order['patch_label'].values
        for i in range(1, n_patches):
            if labels_arr[i] != labels_arr[i - 1]:
                ax1.axhline(i - 0.5, color='black', linewidth=0.5,
                            linestyle='--', alpha=0.5)
    else:
        ax1.set_ylabel("Patch number")
        ax1.yaxis.set_major_locator(plt.MultipleLocator(5))
        ax1.yaxis.set_major_formatter(
            plt.FuncFormatter(lambda x, _: int(x) + 1 if x == int(x) else '')
        )

    # x-limits
    ip_min = active_site.groupby('patch_index')['time_since_entry'].min().min()
    time_left = max(ip_min, -50)
    time_right = min(active_site['bar_end'].max() + 10, 300)

    ax1.set_xlim(time_left, time_right)

    # Empty proxy artists so image markers still get 'Tone' / 'Reward' legend entries
    if tone_img is not None:
        ax1.scatter([], [], s=0, label='Tone')
    if reward_img is not None:
        ax1.scatter([], [], s=0, label='Reward')

    # Legend
    handles, labels = ax1.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax1.legend(by_label.values(), by_label.keys(), loc='upper right')

    if save:
        save.savefig(fig)
        plt.close(fig)
    else:
        plt.show()
        return fig, ax1


def plot_condition_comparison(
    general_df,
    variable: str = 'reward_probability',
    experiment: str = None,
    condition: str = 'session_n',
    group_col: str = 'patch_label',
    odor_labels: list = ['Methyl Butyrate', 'Alpha-pinene'],
    color_dict: dict = None,
    ax=None,
    title: str = None,
    save=False,
):
    # Filter
    general_df = general_df.loc[general_df[group_col] != '0'].copy()
    if experiment:
        col = 'experiment' if 'experiment' in general_df.columns else 'stage_name'
        general_df = general_df.loc[general_df[col] == experiment]

    if odor_labels is None:
        odor_labels = sorted(general_df[group_col].unique().tolist())

    standalone = ax is None
    if standalone:
        fig, ax = plt.subplots(figsize=(3, 3))

    # --- Connecting lines ---
    x_map = {label: i * 1.5 for i, label in enumerate(odor_labels)}
    for session, sdf in general_df.groupby(condition):
        pts = (
            sdf.groupby(group_col)[variable].mean()
            .reindex(odor_labels).dropna()
        )
        if len(pts) == 2:
            ax.plot([x_map[l] for l in pts.index], pts.values,
                    color='gray', alpha=0.4, linewidth=0.5, marker='')

    # --- Mean + SEM dots ---
    for label in odor_labels:
        subset = general_df.loc[general_df[group_col] == label, variable].dropna()
        if subset.empty:
            continue
        mean_val = subset.mean()
        sem_val  = subset.std()
        color    = color_dict[label] if color_dict and label in color_dict else None
        ax.errorbar(
            x_map[label], mean_val,
            yerr=sem_val,
            fmt='o', color=color,
            capsize=0, capthick=0, elinewidth=0.5,
            markersize=3, zorder=10,
        )

    # --- Formatting (set xlim before significance so transform works) ---
    x_vals = list(x_map.values())
    x_center = (min(x_vals) + max(x_vals)) / 2
    half_span = (max(x_vals) - min(x_vals)) / 2 + 0.7
    ax.set_xlim(x_center - half_span, x_center + half_span)
    ax.set_xticks([x_map[l] for l in odor_labels])
    ax.set_xticklabels(odor_labels)
    ax.set_ylabel(variable.replace('_', ' '))
    ax.set_xlabel('')
    if variable == 'reward_probability':
        ax.set_ylim(0, 1 + 0.05)
        ax.set_yticks([0, 0.5, 1])

    if title:
        ax.set_title(title)
    sns.despine(ax=ax, bottom=True)

    # --- Significance ---
    g1 = general_df.loc[general_df[group_col] == odor_labels[0], variable].dropna()
    g2 = general_df.loc[general_df[group_col] == odor_labels[1], variable].dropna()
    try:
        _, p = ttest_rel(g1, g2, nan_policy='omit')
    except:
        _, p = ttest_ind(g1, g2, nan_policy='omit')

    if p < 0.001:   sig = '***'
    elif p < 0.01:  sig = '**'
    elif p < 0.05:  sig = '*'
    else:           sig = 'ns'

    # Convert dot x positions from data to axes coordinates
    ax.figure.canvas.draw()  # force layout so transforms are valid
    inv = ax.transData + ax.transAxes.inverted()
    x0_ax = inv.transform((x_map[odor_labels[0]], 0))[0]
    x1_ax = inv.transform((x_map[odor_labels[1]], 0))[0]

    line = Line2D([x0_ax, x0_ax, x1_ax, x1_ax], [0.92, 0.95, 0.95, 0.92],
                  transform=ax.transAxes, color='black',
                  solid_joinstyle='miter', solid_capstyle='butt')
    ax.add_line(line)
    ax.text((x0_ax + x1_ax) / 2, 0.96, sig, ha='center', va='bottom',
            transform=ax.transAxes)

    if standalone:
        plt.tight_layout()
        if save:
            plt.savefig(save, format='pdf')
        else:
            plt.show()
            plt.close()
