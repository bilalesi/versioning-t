from sqlalchemy.orm import sessionmaker
from sqlalchemy_continuum import version_class

from .model import Agent, ReconstructionMorphology, engine

Session = sessionmaker(bind=engine)
session = Session()


# create an agent
agent = Agent(name="Agent bil")
session.add(agent)
session.commit()

# create a ReconstructionMorphology entity
rm = ReconstructionMorphology(
    description="Sample description",
    name="Sample Name",
    createdBy=agent,
)
session.add(rm)
session.commit()

rm = session.query(ReconstructionMorphology).first()
agent = session.query(Agent).first()

agent2 = Agent(name="Agent sam")
session.add(agent2)
session.commit()

# update description
rm.description = "Updated description 7"
rm.updated_by = agent2
session.commit()

ReconstructionMorphologyVersion = version_class(ReconstructionMorphology)
versions = session.query(ReconstructionMorphologyVersion).all()
print(versions[0].changeset)
