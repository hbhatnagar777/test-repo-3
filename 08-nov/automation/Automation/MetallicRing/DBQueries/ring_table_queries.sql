
DROP TABLE IF EXISTS MetallicRingCS;
DROP TABLE IF EXISTS MetallicRingWC;
DROP TABLE IF EXISTS MetallicRingWS;
DROP TABLE IF EXISTS MetallicRingIS;
DROP TABLE IF EXISTS MetallicRingMA;
DROP TABLE IF EXISTS MetallicRingNWP;
DROP TABLE IF EXISTS MetallicRingErrorDescription;
DROP TABLE IF EXISTS MetallicRingConfigMap;
DROP TABLE IF EXISTS MetallicRingConfig;
DROP TABLE IF EXISTS MetallicRingMail;
DROP TABLE IF EXISTS MetallicRingInfo;
DROP TABLE IF EXISTS MetallicHubRulePriority;
DROP TABLE IF EXISTS MetallicAvailableRing;

CREATE TABLE IF NOT EXISTS MetallicRingInfo(id INTEGER PRIMARY KEY AUTOINCREMENT, rid nvarchar(5) NOT NULL,
			name nvarchar(100), status INT DEFAULT 0);

CREATE TABLE IF NOT EXISTS MetallicRingCS(id INTEGER PRIMARY KEY AUTOINCREMENT, clientid INT, name longtext,  created BIGINT,
rid nvarchar(5) NOT NULL, FOREIGN KEY(rid) REFERENCES MetallicRingInfo(rid));

CREATE TABLE IF NOT EXISTS MetallicRingWC(id INTEGER PRIMARY KEY AUTOINCREMENT, clientid INT, name longtext, created BIGINT,
rid nvarchar(5) NOT NULL, FOREIGN KEY(rid) REFERENCES MetallicRingInfo(rid));

CREATE TABLE IF NOT EXISTS MetallicRingWS(id INTEGER PRIMARY KEY AUTOINCREMENT, clientid INT, name longtext,  created BIGINT,
rid nvarchar(5) NOT NULL, FOREIGN KEY(rid) REFERENCES MetallicRingInfo(rid));

CREATE TABLE IF NOT EXISTS MetallicRingIS(id INTEGER PRIMARY KEY AUTOINCREMENT, index_server longtext, clientid INT, name longtext,  created BIGINT,
rid nvarchar(5) NOT NULL, FOREIGN KEY(rid) REFERENCES MetallicRingInfo(rid));

CREATE TABLE IF NOT EXISTS MetallicRingMA(id INTEGER PRIMARY KEY AUTOINCREMENT, clientid INT, name longtext,  created BIGINT,
rid nvarchar(5) NOT NULL, FOREIGN KEY(rid) REFERENCES MetallicRingInfo(rid));

CREATE TABLE IF NOT EXISTS MetallicRingNWP(id INTEGER PRIMARY KEY AUTOINCREMENT, clientid INT, name longtext, created BIGINT,
rid nvarchar(5) NOT NULL, FOREIGN KEY(rid) REFERENCES MetallicRingInfo(rid));

CREATE TABLE IF NOT EXISTS MetallicRingConfig(id INT NOT NULL PRIMARY KEY, name longtext, created BIGINT, Modified BIGINT);

CREATE TABLE IF NOT EXISTS MetallicRingConfigMap(id INTEGER PRIMARY KEY AUTOINCREMENT, state INT DEFAULT 0,
			startTime BIGINT, endTime BIGINT, rid nvarchar(5) NOT NULL,	errorDesc longtext, cid INT NOT NULL,
			FOREIGN KEY(rid) REFERENCES MetallicRingInfo(rid),
			FOREIGN KEY(cid) REFERENCES MetallicRingConfig(id));

CREATE TABLE IF NOT EXISTS MetallicRingMail(id INTEGER PRIMARY KEY AUTOINCREMENT, sentTo longtext,sentTime BIGINT,
		rid nvarchar(5) NOT NULL, FOREIGN KEY(rid) REFERENCES MetallicRingInfo(rid));

CREATE TABLE IF NOT EXISTS MetallicHubRulePriority(priority INTEGER);

CREATE TABLE IF NOT EXISTS MetallicHubSubnetInfo(id INTEGER PRIMARY KEY AUTOINCREMENT, subnet INTEGER,
            rid nvarchar(5) DEFAULT NULL);

CREATE TABLE IF NOT EXISTS MetallicAvailableRing(rid INTEGER, name longtext, user longtext, status INTEGER);