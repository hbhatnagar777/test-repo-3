# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Default SQL Query templates for TestCases"""

from datetime import datetime
from functools import reduce

from AutomationUtils.logger import get_log
from Web.Common.exceptions import CVTestStepFailure


class ValueProcessors:

    """
    This class contains all the methods that can be used to
    process the dictionary entries
    """

    @staticmethod
    def none(iterable):
        return iterable

    @staticmethod
    def string(iterable):
        return [str(x) for x in iterable]

    @staticmethod
    def lower_string(iterable):
        return [str(x).lower() for x in iterable]

    @staticmethod
    def unique(iterable):
        return set(iterable)

    @staticmethod
    def lower_and_unique(iterable):
        return set(ValueProcessors.lower_string(iterable))


class SQLQueries:
    """Class containing predefined queries"""
    @classmethod
    def sql_server_q1(cls, top=5):
        """
        SQL Server Query 1
        """
        return f"""
            DECLARE @i BIGINT = 0
            DECLARE @seed_time BIGINT = 718007400
            DECLARE @tmp TABLE
            (
                id BIGINT IDENTITY,
                text_t AS 'Text' + RIGHT (
                    '00000000' + CAST(id * 7 + id AS VARCHAR(8)), 8
                ) PERSISTED,
                datetime_t DATETIME,
                timestamp_t BIGINT
            )
            WHILE @i < 1000
            BEGIN
                SET @seed_time = @seed_time + 2000
                INSERT INTO @tmp (datetime_t, timestamp_t) VALUES
                (DATEADD(SECOND, @seed_time, '1970-01-01'), @seed_time)
                SET @i = @i + 1
            END
            SELECT TOP {top} *
            FROM @tmp
            ORDER BY id
            """

    @classmethod
    def sql_server_q2(cls, top=30):
        """SQL server query 2"""
        return f"""
            DECLARE @seed_time BIGINT = 0
            DECLARE @step INT = 1
            DECLARE @number INT = 1
            DECLARE @tmp_var INT = 0
            DECLARE @limit BIGINT = -1000000000
            DECLARE @string1 AS VARCHAR(20) = 'Big'
            DECLARE @string2 AS VARCHAR(20) = 'Flat'
            DECLARE @string3 AS VARCHAR(20) = 'Earth'
            DECLARE @mash AS VARCHAR(60)
            DECLARE @date_today DATETIME = GETDATE()
            DECLARE @tmp TABLE
            (
                id BIGINT IDENTITY,
                number INT,
                text VARCHAR(60),
                datetime_t DATETIME
            )
            WHILE @seed_time > @limit
            BEGIN
                SET @tmp_var += 1
                SET @mash =
                CASE @tmp_var
                    WHEN 1 THEN @string1 + ' ' + @string2 + ' ' + @string3
                    WHEN 2 THEN @string3 + ' ' + @string1 + ' ' + @string2
                    WHEN 3 THEN @string2 + ' ' + @string3 + ' ' + @string1
                END
                INSERT INTO @tmp (datetime_t, text, number) VALUES
                (DATEADD(second, @seed_time, @date_today),@mash, @number)
                SET @seed_time -= @step
                SET @step *=2
                IF (@tmp_var = 3)
                BEGIN
                   SET @number += 1
                   SET @tmp_var = 0
                END
            END
            SELECT TOP {top} *
            FROM @tmp
            ORDER BY id"""

    @classmethod
    def sql_server_r1(cls, top=5, value_processor=ValueProcessors.none):
        """SQL Server Query 1 result"""
        ids = list(range(1, top + 1))
        timestamps = reduce(
            lambda seed, i: seed + [seed[-1] + 2000],
            ids,
            [718007400]
        )[1:]  # [1:] is to remove the seed value
        data = {
            "datetime_t": [
                datetime.utcfromtimestamp(timestamp).strftime(
                    "%b %#d, %Y, %I:%M:%S %p"
                )
                for timestamp in timestamps
            ],
            "id": ids,
            "text_t": ["Text{0:08d}".format(i * 8) for i in ids],
            "timestamp_t": timestamps
        }
        return {
            k: value_processor(data[k])
            for k in data
        }

    @classmethod
    def validate_equality(
            cls, expected, received, value_processor=ValueProcessors.none,
            err_msg="Expected and received values are not equal"):
        """Check if the two dictionaries are equal"""
        expected_ = {
            str(k): value_processor(expected[k])
            for k in expected.keys()
        }
        received_ = {
            str(k): value_processor(received[k])
            for k in received.keys()
        }
        if expected_ != received_:
            info = (f"\nExpected - [{str(expected_)}]"
                    f"\nReceived - [{str(received_)}]")
            get_log().info(info)

            raise CVTestStepFailure(err_msg + info)

    @classmethod
    def validate_membership_equality(
            cls, expected, received, value_processor=ValueProcessors.none,
            err_msg="Expected and received values are not equal"):
        """Check if the one dictionary contains the value in the other dictionary under the same key"""
        expected_ = {
            str(k): value_processor(expected[k])
            for k in expected.keys()
        }
        received_ = {
            str(k): value_processor(received[k])
            for k in received.keys()
        }
        for key in expected_:
            if isinstance(expected_[key], str):
                if expected_[key] in received_[key]:
                    continue
            elif expected_[key] == received_[key]:
                continue
            else:
                info = (f"\nExpected - [{str(expected_)}]"
                        f"\nReceived - [{str(received_)}]")
                get_log().info(info)
                print(expected_[key], received_[key])
                raise CVTestStepFailure(err_msg + info)

    @classmethod
    def validate_list_equality(cls, expected, received, value_processor=ValueProcessors.none,
                               err_msg="Expected and received lists are not equal"):
        """Validates Equality of the lists"""
        expected_ = [value_processor(value) for value in expected]
        received_ = [value_processor(value) for value in received]

        if expected_ != received_:
            info = (f"\nExpected {len(expected)} rows with values {expected}"
                    f"\nActually received {len(received)} rows with values {received}")
            get_log().info(info)
            raise CVTestStepFailure(err_msg + info)

    @classmethod
    def mysql_q(cls):
        """MySQL Query"""
        return """
        SELECT 1 AS 'ID', 'A' AS 'Char', '1A' AS 'String'
        UNION ALL
        SELECT 2, 'B', '2B'
        UNION ALL
        SELECT 3, 'C', '3C'
        """

    @classmethod
    def mysql_r(cls):
        """MySQL Result"""
        return {
            "ID": ["1", "2", "3"],
            "Char": ["A", "B", "C"],
            "String": ["1A", "2B", "3C"]
        }

    @classmethod
    def oracle_q(cls):
        """Oracle SQL"""
        return """
        SELECT 1 AS ID, 'A' AS Char_t, '1A' AS String_t
        FROM DUAL
        UNION ALL
        SELECT 2, 'B', '2B'
        FROM DUAL
        UNION ALL
        SELECT 3, 'C', '3C'
        FROM DUAL
        """

    @classmethod
    def oracle_r(cls):
        """Oracle Result"""
        return {
            "ID": ["1", "2", "3"],
            "CHAR_T": ["A", "B", "C"],
            "STRING_T": ["1A", "2B", "3C"]
        }
