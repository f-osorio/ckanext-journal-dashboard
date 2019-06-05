html = u"""
<html>
    <head>
        <style>
            body {{
                font-family: Arial,Helvetica Neue,Helvetica,sans-serif;

            }}
            table {{
                border: 1px solid black;
                table-layout: fixed;
                border-collapse: collapse;
                text-align:center;
                padding-right: 5px;
                padding-left: 5px;
            }}

            .heading {{
                border-bottom: 1px solid black;
            }}

            .dataset_name {{
                background: #8caef7;
            }}

            h1 {{
                font-size: 18px;
            }}
        </style>
    </head>
    <body>
        <h1>Access Summary for the "{journal}"</h1>

        <p>Dear Editor,</p>
        <p>Please find below some accumulated statistics for the {journal}</p>

        <table style="text-align: center; width: 50%; border: 1px solid black; margin-right: 25%; margin-left: 25%;">
            <thead style="font-weight:bold;">
                <tr>
                    <td>Datasets</td>
                    <td>Resources</td>
                    <td>Monthly Views</td>
                    <td>Total Views</td>
                    <td>Monthly Downloads</td>
                    <td>Total Downloads</td>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>{package_num}</td>
                    <td>{package_resources}</td>
                    <td>{package_view_monthly}</td>
                    <td>{package_view_total}</td>
                    <td>{package_download_monthly}</td>
                    <td>{package_download_total}</td>
                </tr>
            </tbody>
        </table>

        <p>
            Below, you will find more detailed statistcs regarding the views of each data submission (landing page) and the downloads of each file for these submissions (e.g. datasets).
        </p>

        <p>
            Kind regards from the ZBW Journal Data Archive.
        </p>

        <h3>Summary of Data Submissions & Resources:</h3>
        {main_table}

        <p>
            * A data submission is characterised with 'false' if it has not been published yet. This indicates that a submission is in a 'private' state or 'in review.' Individual resources only appear for published data submissions.
        </p>
    </body>
</html>
       """

text = u"""
Dear Editor,

Below is a summary of the access to "{journal}"

--Journal Summary--
Datasets: {package_num}
Resources: {package_resources}
Monthyly Views: {package_view_monthly}
Total Views: {package_view_total}
Monthly Downloads: {package_download_monthly}
Total Downloads: {package_download_total}

--Dataset Breakdown--{packages_text}

"""
