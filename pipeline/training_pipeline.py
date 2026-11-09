from src.data_ingestion import DataIngestion
from src.data_preprocessing import DataProcessor
from src.model_trainer import ModelTrainer

if __name__ == "__main__":
    # Data Ingestion
    data_ingestion = DataIngestion()
    data_ingestion.run()

    # Data Preprocessing
    data_preprocessor = DataProcessor()
    data_preprocessor.run()

    # Model Trainer
    model_trainer = ModelTrainer()
    model_trainer.run()
