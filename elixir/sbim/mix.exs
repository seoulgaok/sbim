defmodule Sbim.MixProject do
  use Mix.Project

  # 판은 python/pyproject.toml 과 같이 올린다
  @version "0.1.4"

  def project do
    [
      app: :sbim,
      version: @version,
      elixir: "~> 1.18",
      start_permanent: Mix.env() == :prod,
      deps: deps(),
      description: "sbim 데이터 표준 — pydantic 정본에서 생성한 BuildOptions·scheme 계약"
    ]
  end

  def application do
    [extra_applications: [:logger, :crypto]]
  end

  # jason 은 테스트가 fixtures·samples JSON 을 읽는 데만 쓴다
  defp deps do
    [{:jason, "~> 1.4", only: :test}]
  end
end
