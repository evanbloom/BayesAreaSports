import pandas as pd
import sqlite3
import scipy.stats

class predicter (object):

    def __init__(self, db_path):
        self.db_path = db_path

    @staticmethod
	def rescale_parameters(alpha, beta, total):
	    cur_scale = alpha + beta
	    rescale = total / cur_scale
	    return alpha * rescale, beta * rescale

	def fit_beta (self, min_percentile, max_percentile, prior_games):
	    qry_str = "SELECT pct FROM historical WHERE percentile BETWEEN {0} AND {1} AND game = 82". \
	        format(str(min_percentile), str(max_percentile))
	    conn = sqlite3.connect(self.db_address )
	    win_pct = pd.read_sql(qry_str, conn)
	    fitted = scipy.stats.beta.fit(win_pct, floc =0 , fscale = 1)
	    alpha, beta = predicter.rescale_parameters (fitted[0], fitted[1], prior_games)
	    return alpha, beta

	@staticmethod
	def create_params (p, N):
	    alpha = p*N
	    beta = (1-p) *N
	    return alpha, beta
    
    @staticmethod
	def cdf_record (alpha, beta, cur_wins, cur_losses, n_games = 82 ):
	    remaining_games = n_games - (cur_wins + cur_losses)
	    more_wins = range(remaining_games + 1)
	    out = {'wins':[],'prob':[]}
	    for win in more_wins:
	        remaining_pct = win*1.0 / remaining_games
	        prob = scipy.stats.beta.sf(remaining_pct, alpha , beta)
	        out['wins'].append(cur_wins + win)
	        out['prob'].append(round(prob,4)*100)
	    return pd.DataFrame.from_dict(out)
    @staticmethod
	def custom_projection (p, N, cur_wins, cur_losses, n_games = 82):
	    alpha, beta = create_params(p,N)
	    return cdf_record (alpha, beta, cur_wins, cur_losses, n_games = 82 )

	def lookup_current (self, team):
	    conn = sqlite3.connect(self, db_address )
	    qry_str = 'SELECT wins, losses FROM current WHERE short = "{0}"'.format(team)
	    out = pd.read_sql(qry_str, conn)
	    return out.wins[0], out.losses[0]
	    
	def update_projection (self, min_percentile, max_percentile, prior_games, current_team):
	    # emperical priors
	    alpha, beta = self.fit_beta(min_percentile, max_percentile, prior_games)
	    ## get current record of team
	    wins, losses = self.lookup_current (current_team)
	    ## updated priors
	    alpha_prime = alpha + wins
	    beta_prime = beta + losses
	    return predictor.cdf_record (alpha_prime, beta_prime, wins, losses)
    