from datetime import datetime
from sqlalchemy.orm import reconstructor, relationship, backref
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.types import Integer, Unicode, Boolean, DateTime
from sqlalchemy import BigInteger
from sqlalchemy.sql.expression import false, or_
from sqlalchemy.ext.associationproxy import association_proxy

from flask.ext.login import current_user

from openspending.core import db

from openspending.model.source import Source
from openspending.model.dataorg import DataOrg
from openspending.model import Account
from openspending.model.common import (MutableDict, JSONType,
                                       DatasetFacetMixin)


dataview_dataset_table = Table(
    'dataview_dataset', db.metadata,
    Column('dataview_id', Integer, ForeignKey('dataview.id'),
           primary_key=True),
    Column('dataset_id', Integer, ForeignKey('dataset.id'),
           primary_key=True)
)

def make_uuid():
    return unicode(uuid.uuid4())

class Dataview(db.Model):

    """ The dataset is the core entity of any access to data. All
    requests to the actual data store are routed through it, as well
    as data loading and model generation.

    """
    __tablename__ = 'dataview'

    id = Column(Integer, primary_key=True)
    title = Column(Unicode(500))
    description = Column(Unicode())


    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    urlhash = Column(Unicode(2000), default=make_uuid)

    datasets = relationship(Dataset,
                            secondary=dataview_dataset_table,
                            backref=backref('dataviews', lazy='dynamic'))

    account_id = Column(Integer, ForeignKey('account.id'))
    account = relationship(Account, backref=backref("dataviews", uselist=False))

    cloned_dataview_id = Column(Integer, ForeignKey('dataview.id'))
    cloned_dataview = relationship(self, backref=backref("clones", lazy='dynamic'))

    settings = Column(MutableDict.as_mutable(JSONType), default=dict)


    def __init__(self, data = None):
        self.urlhash = make_uuid()
        if not data:
            return
        self.title = data.get("title")
        self.description = data.get("description")
        if current_user:
            self.account = current_user
        self.settings = data.get("settings", {})
        self.cloned_dataview = data.get("cloned_dataview", None)



    @classmethod
    def clone_view(cls, theobj):

        fields = ['title', 'description',  
                 'settings', 'datasets', 'settings']
        classobj = cls()
        for field in fields:
            setattr(classobj, field, getattr(theobj, field))

        classobj.cloned_dataview = theobj

        db.session.add(classobj)
        db.session.commit()

        return classobj



    def __repr__(self):
        return "<Dataview(%r,%r)>" % (self.id, self.title)

    def update(self, data):
        #not to update name
        self.title = data.get("title")
        self.description = data.get("description")
        self.datasets = data.get("datasets")
        self.settings = data.get("settings", {})


    def as_dict(self):
        return {
            'title': self.label,
            'description': self.name,
            'settings': self.description,
            'account_id': self.account_id
        }



    @classmethod
    def all_by_account(cls, account, order=True):
        """ Query available datasets based on dataset visibility. """
        return db.session.query(cls).filter_by(account_id=account.id).all()


    @classmethod
    def all(cls, order=True):
        """ Query available datasets based on dataset visibility. """
        q = db.session.query(cls)
        if order:
            q = q.order_by(cls.label.asc())
        return q

    @classmethod
    def by_urlhash(cls, name):
        return db.session.query(cls).filter_by(urlhash=urlhash).first()


    @classmethod
    def by_id(cls, id):
        return db.session.query(cls).filter_by(id=id).first()

