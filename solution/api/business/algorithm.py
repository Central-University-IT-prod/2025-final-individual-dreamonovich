from django.db import connection
from django.db.models import Min, Max

from business.models import Campaign, Score


def normalize(value, min_val, max_val):
    """
    Normalize a value to a 0-1 scale given a minimum and maximum value.

    Parameters:
        value (float): The value to normalize.
        min_val (float): The minimum value in the expected range.
        max_val (float): The maximum value in the expected range.

    Returns:
        float: The normalized value, clamped between 0 and 1.
    """
    if max_val - min_val == 0:
        return 0.0  # Avoid division by zero; or choose another default behavior

    normalized_value = (value - min_val) / (max_val - min_val)
    # Clamp the result to [0, 1]
    return max(0.0, min(1.0, normalized_value))


def compute_profit(campaign, ml_norm):
    # Compute absolute profit P
    P = campaign.cost_per_impression + (ml_norm * campaign.cost_per_click)
    # Determine campaign-specific min and max
    P_min = campaign.cost_per_impression
    P_max = campaign.cost_per_impression + campaign.cost_per_click
    # Normalize P within the campaign's possible range
    P_norm = normalize(P, P_min, P_max)
    return P, P_norm


def compute_revenue_multiplier(P, client_max_P):
    return P / client_max_P if client_max_P > 0 else 1.0


def normalize_ml_score(ml_score, ml_min, ml_max):
    if ml_max > ml_min:
        ml_norm = (ml_score - ml_min) / (ml_max - ml_min)
    elif ml_max == 0:
        ml_norm = 1.0
    else:
        ml_norm = 0  # fallback if no variation
    return ml_norm


def compute_global_over_impression_penalty(
    global_impressions, global_impressions_limit
):
    """
    Compute a global over-impression penalty multiplier.
    For every 5% over the global limit, a penalty of 5% is applied.
    """
    ratio = global_impressions / global_impressions_limit
    if ratio <= 1:
        return 1.0
    else:
        over_percentage = (ratio - 1) * 100  # percentage over limit
        penalty_steps = over_percentage // 5
        return max(0, 1 - 0.05 * penalty_steps)


def compute_over_click_penalty(current_clicks, predicted_click_prob, clicks_limit):
    # Compute the predicted new click count ratio
    new_clicks = current_clicks + predicted_click_prob
    r_C = new_clicks / clicks_limit
    if r_C <= 1:
        return 1.0
    else:
        over_percentage = (r_C - 1) * 100  # in percent
        penalty_steps = over_percentage // 5
        return max(0, 1 - 0.05 * penalty_steps)


def compute_impression_deficit(current_impressions, impressions_limit):
    """
    Compute the impression deficit factor (D) as the fraction of the campaign's
    impression limit that remains. If the campaign has received no impressions, D=1.
    If it has reached or exceeded the limit, D=0.
    """
    impressions_remaining = max(0, impressions_limit - current_impressions)
    return impressions_remaining / impressions_limit if impressions_limit > 0 else 0.0


def compute_ad_score(
    campaign: Campaign,
    client,
    current_impressions,
    current_clicks,
    ml_max,
    ml_score,
    client_max_P,
    ml_min,
):
    ml_norm = normalize_ml_score(ml_score, ml_min, ml_max)
    P, P_norm = compute_profit(
        campaign, ml_norm
    )  # Сначала ищем профит для каждого обьявления, чтобы высчитать max_P
    revenue_multiplier = compute_revenue_multiplier(P, client_max_P)
    profit_component = P_norm * revenue_multiplier

    # Relevancy component is ml_norm
    R = ml_norm

    # Performance component
    new_impressions = current_impressions + 1
    r_I = new_impressions / campaign.impressions_limit
    impression_perf = min(r_I, 1)

    # For clicks, assume predicted click probability = ml_norm (or use a better model)
    predicted_clicks = ml_norm  # simplistic assumption
    r_C = (current_clicks + predicted_clicks) / campaign.clicks_limit
    click_perf = min(r_C, 1)
    T = (impression_perf + click_perf) / 2

    # Base Score using weights
    base_score = 0.525 * profit_component + 0.275 * R + 0.175 * T

    D = compute_impression_deficit(current_impressions, campaign.impressions_limit)

    # Final Score
    final_score = base_score * D
    return final_score

def get_max_profit(client_id, campaign_ids: tuple):
    """
    Computes the maximum profit P for the given client and list of campaign IDs.

    The profit P for a campaign is computed as:
        P = cost_per_impression + (ml_norm * cost_per_click)

    where ml_norm is taken from the business_score table (here assumed to be score/100).
    """
    # Build the SQL query.
    query = """
        SELECT MAX(bc.cost_per_impression + (COALESCE(bs.normalized_ml, 0) * bc.cost_per_click)) AS max_profit
        FROM business_campaign bc
        LEFT JOIN (
            -- Get the normalized ML score for this client per advertiser.
            SELECT advertiser_id, score / 100.0 AS normalized_ml
            FROM business_score
            WHERE client_id = %s
        ) bs
          ON bs.advertiser_id = bc.advertiser_id
        WHERE bc.id IN %s;
    """
    # Execute the query. Note that campaign_ids must be a tuple.
    with connection.cursor() as cursor:
        cursor.execute(
            query, [str(client_id), campaign_ids]
        )  # campaign_ids может быть пустым
        row = cursor.fetchone()
    return row[0] if row and row[0] is not None else 0

def get_max_P(client, campaigns):
    max_P = 0
    for campaign in campaigns:
        P, _ = compute_profit(
            campaign, client.get_normalized_ml_score(campaign.advertiser)
        )
        max_P = P if max_P < P else max_P
    return max_P
