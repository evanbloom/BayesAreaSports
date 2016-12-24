

import pandas as pd
import urllib2
from bs4 import BeautifulSoup
import sqlite3

class ingester (object):

    def __init__(self, db_path):
        self.db_path = db_path

    @staticmethod
    def get_current_records():
        """
        Gets the current records for each NBA team and outputs to DataFrame
        """
        standings_url = "http://www.basketball-reference.com/leagues/NBA_2017.html#site_menu_link"

        response = urllib2.urlopen(standings_url)
        html = response.read()
        soup = BeautifulSoup(html, 'html.parser')
        eastern = soup.find("div", {"id":"all_confs_standings_E"}).find_all("tr", {"class":"full_table"})
        western = soup.find("div", {"id":"all_confs_standings_W"}).find_all("tr", {"class":"full_table"})

        records = {'short':[], 'team':[], 'name':[], 'wins':[], 'losses':[], 'ppg':[], 'papg':[]}
        for row in (eastern + western):
            #Get name and clean name
            name = row.find("th", {"data-stat":"team_name"}).get_text()
            name = str(name[:name.find(u'\xa0')])
            if name[-1]=="*": name = name[:-1]
            team = name.replace(" ","_").lower()
            records['team'].append(team)
            records['name'].append(name)
            #Get Abrev
            url = row.find("a")['href']
            short = url[7:10]
            #wins 
            wins = int(row.find("td", {"data-stat":"wins"}).get_text())
            records['wins'].append(wins)
            #losses
            losses = int(row.find("td", {"data-stat":"losses"}).get_text())
            records['losses'].append(losses)
            #ppg
            ppg = float(row.find("td", {"data-stat":"pts_per_g"}).get_text())
            records['ppg'].append(ppg)
            #papg
            papg = float(row.find("td", {"data-stat":"opp_pts_per_g"}).get_text())
            records['papg'].append(papg)
            ##short
            url = row.find("a")['href']
            short = str(url[7:10])
            records['short'].append(short)
        records_frame = pd.DataFrame.from_dict(records)[["team", "name", "short", "wins","losses","ppg","papg"]]
        records_frame['games'] = records_frame['wins'] + records_frame['losses']
        return records_frame


    @staticmethod
    def get_team_season(team_url):
        """
        Gets the historical records for each NBA team in a season and outputs to DataFrame
        """
        response = urllib2.urlopen(team_url)
        html = response.read()
        soup = BeautifulSoup(html, 'html.parser')
        records = soup.find("div", {"id":"all_games"}).find_all("tr")
        game_dict= {"game":[], "wins":[], "losses":[]}
        for row in records:
            game= row.find("th", {"data-stat":"g"}).get_text()
            if game == "G": #Ignore header rows
                pass
            else:
                game_dict['game'].append(int(game))
                #Get wins
                wins = row.find("td", {"data-stat":"wins"}).get_text()
                game_dict['wins'].append(int(wins))
                # Get losses
                losses = row.find("td", {"data-stat":"losses"}).get_text()
                game_dict['losses'].append(int(losses))
                
        game_frame = pd.DataFrame.from_dict(game_dict)[["game", "wins", "losses"]]
        return game_frame


    @staticmethod
    def get_historical_year(year):
        """
        Gets the historical records for all NBA teams in a season and outputs to DataFrame
        """
        url = "http://www.basketball-reference.com/leagues/NBA_{0}.html".format(str(year))
        response = urllib2.urlopen(url)
        html = response.read()
        soup = BeautifulSoup(html, 'html.parser')
        eastern = soup.find("div", {"id":"all_divs_standings_E"}).find_all("tr", {"class":"full_table"})
        western = soup.find("div", {"id":"all_divs_standings_W"}).find_all("tr", {"class":"full_table"})
        info = []
        for row in (eastern + western):
            name = row.find("th", {"data-stat":"team_name"}).get_text()
            name = str(name[:name.find(u'\xa0')])
            if name[-1]=="*": name = name[:-1]
            team = name.replace(" ","_").lower()
            url = row.find("a")['href']
            short = str(url[7:10])
            info.append((team, short))
        frames = []
        for team in info:
            url = "http://www.basketball-reference.com/teams/{0}/{1}_games.html".format(team[1],year)
            team_season = ingester.get_team_season(url)
            team_season['team'] = str(team[0])
            team_season['short']= str(team[1])
            team_season['year'] = int(year)
            frames.append(team_season)
        season  = pd.concat(frames)
        season.reset_index(drop=True, inplace=True)
        season['pct'] = season.wins/season.game*1.0
        season['percentile'] = season.groupby('game')['pct'].rank(ascending=False, pct=True, method ="first")
        return season

    @staticmethod
    def get_historical(years):
        """
        Gets the historical records for all NBA teams in a range of seasons and outputs to DataFrame
        """
        results = []
        for year in years:
            result = ingester.get_historical_year(year)
            results.append(result)
        historical_frame = pd.concat(results)[["year", "team", "short", "game", "wins", "losses"]]
        return historical_frame


    def init_database (self, years):
        """
        Initializes a database, for a set of seasons
        """
        conn = sqlite3.connect(self.db_path)
        historical = ingester.get_historical(years)
        historical.to_sql("historical", conn, index=False, if_exists='replace')
        current = ingester.get_current_records()
        current.to_sql("current", conn, index=False, if_exists='replace')

    def add_years(self, years):
        """
        Adds additional years to the historical record
        """
        conn = sqlite3.connect(self.db_path)
        qry_str = "SELECT DISTINCT year FROM historical"
        present_years = pd.read_sql(qry_str, conn)['year'].tolist()
        years_toget =  [x for x in years if x not in present_years]
        historical = ingester.get_historical(years_toget)
        historical.to_sql("historical", conn, index=False, if_exists='append')
        
    def add_current (self):
        """
        Updates the current records for a database
        """
        conn = sqlite3.connect(self.db_path )
        qry_str = "SELECT * FROM current"
        all_current = pd.read_sql(qry_str, conn)
        current = ingester.get_current_records()
        all_current = pd.concat([all_current, current])
        all_current.drop_duplicates(inplace=True)
        all_current.to_sql("current", conn, index=False, if_exists='replace')

