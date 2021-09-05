import json
from rewards.classes.Schedule import Schedule
from rewards.aws.analytics import upload_analytics, upload_schedules

class CycleLogger:
    
    def __init__(self):
        self.schedules = {}
        self.settData = {}
        self.treeDistributions = {}
        self.userData = {}
        
    def add_schedule(self, s: Schedule, sett: str):
        """Add schedule for sett

        :param s: schedule to add
        :param sett: sett for schedule
        """
        if sett not in self.schedules:
            self.schedules[sett] = []
        self.schedules[sett].append(s.asdict())
        
    def add_user_data(self, addr: str, token: str, amount: float, sett: str):
        """Add user data

        :param addr: user address
        :param token: token to add
        :param amount: amount of token
        :param sett: sett where rewards come from
        """
        if addr not in self.userData:
            self.userData[addr] = {}
        if sett not in self.userData[addr]:
            self.userData[addr][sett] = {}
        if token not in self.userData[addr][sett]:
            self.userData[addr][sett][token] = 0
        self.userData[addr][sett][token] = amount
            
            
    def add_sett_data(self, sett: str, token: str, amount: float):
        """Add total rewards from a sett

        :param sett: sett to add rewards
        :param token: token to add:
        :param amount: amount of token
        """
        if sett not in self.settData:
            self.settData[sett] = {}
        if token not in self.settData[sett]:
            self.settData[sett][token] = 0
            
        self.settData[sett][token] = amount
        
    def add_tree_distribtion(self, treeDistribution, sett: str):
        """Add tree distribution

        :param treeDistribtion: tree distribtion to add:
        :param sett: sett where distribution comes from:
        """
        if sett not in self.treeDistributions:
            self.treeDistributions[sett] = []
        self.treeDistributions[sett].append(treeDistribution)
        
    def save(self, cycle: int):
        """Save analytics and schedules

        :param cycle: current rewards cycle
        """
        upload_analytics(cycle, {
            "settData": self.settData,
            "treeDistributions": self.treeDistributions,
            "userData": self.add_user_data,
        })
        upload_schedules(self.schedules)

        
        