class Orchestrator:
    def __init__(self,catalog,logger):
        self.catalog,self.logger=catalog,logger
    def execute(self,c):
        for step in c["config"]["pipeline"]:
            plugin=self.catalog.resolve(step)
            c=self.logger.run(c["execution_id"],c["config"]["model"]["name"],
                              step,plugin.run,c)
        return c
