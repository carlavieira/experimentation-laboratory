import os
import dotenv
import pandas as pd
from github import Github


dotenv.load_dotenv(dotenv.find_dotenv())
TOKEN = os.getenv("GITHUB_ACCESS_TOKEN")

print("\n****  Starting Cloning Process *****\n")

github = Github("admited", TOKEN)
github_user = github.get_user()

nodes = pd.read_csv(os.path.abspath(os.getcwd()) + "/export_dataframe.csv")


for index, row in nodes.iterrows():
    if (str(row['CBO'])=="nan" or str(row['DIT'])=="nan" or str(row['WMC'])=="nan" or str(row['LOC'])=="nan"):
        try:
            original_repo = github.get_repo(row['Owner/Repository'])
            cmd = "git clone {}".format(original_repo.clone_url)
            print("Starting to clone {}. The {}th repo...".format(original_repo.name, index))
            print("Running command '{}'".format(cmd))

            os.system(cmd)
            print("Finished cloning {}".format(original_repo.name))

            print("Calculating metrics..")
            cmd = "java -jar ck.jar {}/{}/ 1 0 0".format(os.path.abspath(os.getcwd()), original_repo.name)
            success = os.system(cmd)
            # Leitura do csv criado pelo CK, selecionando apenas as colunas que importam para o estudo
            metrics_df = pd.read_csv(os.path.abspath(os.getcwd()) + "/class.csv", usecols=['cbo', 'dit', 'wmc', 'loc'])
            # Cálculo das medianas de cada métrica do repositório atual
            medians = metrics_df.median(skipna=True)
            """
            Se definirmos skipna=True, ele ignora a NaN no campo de dados.
            Isto nos permite calcular a mediana do DataFrame ao longo do eixo da coluna, ignorando os valores NaN.
            """
            # Adicionando os valores calculados no DataFrame principal na linha correspondente ao repositório
            nodes.loc[index, 'CBO'] = medians['cbo']
            nodes.loc[index, 'DIT'] = medians['dit']
            nodes.loc[index, 'WMC'] = medians['wmc']
            nodes.loc[index, 'LOC'] = medians['loc']

            # Comando para apagar o repositório clonado a cada iteração
            cmd = "rm -rf {}".format(original_repo.name)
            os.system(cmd)
            print("Finished removing {}".format(original_repo.name))
            print("#####################################")
            print("")
            if success != 0:
                raise Exception("Error when apply metrics...")
            print(f"Saving metrics for {original_repo.name}: CBO={medians['cbo']}, DIT={medians['dit']}, WMC={medians['wmc']}, LOC={medians['loc']}.")
            nodes.to_csv(os.path.abspath(os.getcwd()) + f'/dataframe_with_metrics.csv', index=False, header=True)

        except Exception as e:
            cmd = "rm -rf {}".format(original_repo.name)
            os.system(cmd)
            print("Finished removing {}".format(original_repo.name))
            print("#####################################")
            print('Failure at repo {}'.format(original_repo.name))
            print(e)


nodes.to_csv(os.path.abspath(os.getcwd()) + f'/dataframe_with_metrics.csv', index=False, header=True)
print("Metrics Calculated Successfully! Saved csv with mining results")
